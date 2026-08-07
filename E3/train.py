# -*- coding: utf-8 -*-
"""
E3/train.py — Entrenamiento del modelo PCN (Point Completion Network).

Modelo: PCN (Yuan et al., 2018) — encoder PointNet + decoder coarse/fine con folding.
Pérdida: Chamfer Distance CD-L1 (media de mínimas distancias euclídeas).

USO (siempre desde la raíz del repo c:/EDF/TFM):
  python -m E3.train                               # todo por defecto, 100 épocas
  python -m E3.train --epochs 2                    # smoke-test rápido
  python -m E3.train --epochs 50 --lr 0.0005
  python -m E3.train --resume E3/checkpoints/best.pt

  En CPU puede tardar horas a 100 épocas — empieza con --epochs 2 para
  verificar que funciona antes del run largo.

SALIDAS
  E3/checkpoints/epoch_NNN.pt   checkpoint periódico (cada --guardar_cada épocas)
  E3/checkpoints/best.pt        mejor modelo según val loss
"""

import argparse
import math
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.optim.lr_scheduler import StepLR

from E3.dataset import construir_dataloaders


# ---------------------------------------------------------------------------
# CHAMFER DISTANCE
# ---------------------------------------------------------------------------

def chamfer_distance(pred: torch.Tensor, gt: torch.Tensor) -> torch.Tensor:
    """Chamfer Distance CD-L1 (distancias euclídeas, no al cuadrado).

    CD(A, B) = mean_{a∈A} min_{b∈B} ||a−b|| + mean_{b∈B} min_{a∈A} ||a−b||

    cdist con p=2 devuelve norma euclídea (no squared) → CD-L1.
    Los números de pérdida no son comparables directamente con papers
    que usan CD-L2 (distancias al cuadrado).

    pred, gt: (B, N, 3)   — pueden tener distinto N
    """
    dist = torch.cdist(pred, gt, p=2)                       # (B, N_pred, N_gt)
    loss_pred_to_gt = dist.min(dim=2).values.mean()
    loss_gt_to_pred = dist.min(dim=1).values.mean()
    return (loss_pred_to_gt + loss_gt_to_pred) / 2


# ---------------------------------------------------------------------------
# MODELO PCN
# ---------------------------------------------------------------------------

class PCNEncoder(nn.Module):
    """Encoder PointNet en dos pasos con concatenación de feature global."""

    def __init__(self):
        super().__init__()
        self.layer1 = nn.Sequential(
            nn.Conv1d(3, 128, 1), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Conv1d(128, 256, 1),
        )
        self.layer2 = nn.Sequential(
            nn.Conv1d(512, 512, 1), nn.BatchNorm1d(512), nn.ReLU(),
            nn.Conv1d(512, 1024, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, N, 3) → transponer a (B, 3, N) para Conv1d
        x = x.transpose(1, 2)                                      # (B, 3, N)
        feat1 = self.layer1(x)                                     # (B, 256, N)
        global1 = feat1.max(dim=2).values                          # (B, 256)
        feat1_exp = global1.unsqueeze(2).expand(-1, -1, feat1.size(2))
        feat2_in = torch.cat([feat1, feat1_exp], dim=1)            # (B, 512, N)
        feat2 = self.layer2(feat2_in)                              # (B, 1024, N)
        return feat2.max(dim=2).values                             # (B, 1024)


class PCNDecoderCoarse(nn.Module):
    """Feature global → nube de puntos coarse (primer nivel de reconstrucción)."""

    def __init__(self, n_coarse: int = 512):
        super().__init__()
        self.n_coarse = n_coarse
        self.mlp = nn.Sequential(
            nn.Linear(1024, 1024), nn.ReLU(),
            nn.Linear(1024, 1024), nn.ReLU(),
            nn.Linear(1024, n_coarse * 3),
        )

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        # feat: (B, 1024) → (B, n_coarse, 3)
        return self.mlp(feat).reshape(feat.size(0), self.n_coarse, 3)


class FoldingDecoder(nn.Module):
    """Expande cada punto coarse con una rejilla 2D fija → nube fine.

    Cada punto coarse genera folding_u² puntos finos a su alrededor.
    Con n_coarse=512 y folding_u=2: 512 × 4 = 2048 puntos finos,
    lo que coincide con el contrato E3→E4.
    """

    def __init__(self, n_coarse: int = 512, folding_u: int = 2):
        super().__init__()
        self.n_coarse = n_coarse
        self.n_per_coarse = folding_u * folding_u  # 4

        # Rejilla 2D fija (no aprendida) — mismos desplazamientos locales para todos
        ux = torch.linspace(-0.05, 0.05, folding_u)
        gx, gy = torch.meshgrid(ux, ux, indexing="ij")
        self.register_buffer("grid", torch.stack([gx.flatten(), gy.flatten()], dim=1))
        # self.grid: (n_per_coarse, 2)

        # MLP por punto fino: 1024 (global) + 3 (coarse xyz) + 2 (grid) → 3 (offset)
        self.mlp = nn.Sequential(
            nn.Conv1d(1029, 512, 1), nn.BatchNorm1d(512), nn.ReLU(),
            nn.Conv1d(512, 256, 1),  nn.BatchNorm1d(256), nn.ReLU(),
            nn.Conv1d(256, 3, 1),
        )

    def forward(self, feat: torch.Tensor, coarse: torch.Tensor) -> torch.Tensor:
        # feat:   (B, 1024)
        # coarse: (B, n_coarse, 3)
        B = feat.size(0)
        n_fine = self.n_coarse * self.n_per_coarse  # 2048

        # 1. Feature global repetida: (B, 1024) → (B, n_fine, 1024)
        feat_exp = feat.unsqueeze(1).expand(-1, n_fine, -1)

        # 2. Cada punto coarse repetido n_per_coarse veces: (B, n_coarse, 3) → (B, n_fine, 3)
        coarse_rep = (coarse.unsqueeze(2)
                            .expand(-1, -1, self.n_per_coarse, -1)
                            .reshape(B, n_fine, 3))

        # 3. Rejilla repetida n_coarse veces: (n_per_coarse, 2) → (B, n_fine, 2)
        grid_rep = (self.grid.unsqueeze(0)
                             .expand(self.n_coarse, -1, -1)
                             .reshape(n_fine, 2)
                             .unsqueeze(0)
                             .expand(B, -1, -1))

        # 4. MLP → offset 3D para cada punto fino
        combined = torch.cat([feat_exp, coarse_rep, grid_rep], dim=2)  # (B, n_fine, 1029)
        offset = self.mlp(combined.transpose(1, 2)).transpose(1, 2)    # (B, n_fine, 3)

        return coarse_rep + offset  # (B, n_fine, 3)


class PCN(nn.Module):
    """PCN completo: nube parcial → (coarse, fine).

    Input:  (B, 2048, 3) nube parcial
    Output: coarse (B, 512, 3) + fine (B, 2048, 3)
    """

    def __init__(self, n_coarse: int = 512, folding_u: int = 2):
        super().__init__()
        self.encoder       = PCNEncoder()
        self.decoder_coarse = PCNDecoderCoarse(n_coarse)
        self.decoder_fine   = FoldingDecoder(n_coarse, folding_u)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feat   = self.encoder(x)
        coarse = self.decoder_coarse(feat)
        fine   = self.decoder_fine(feat, coarse)
        return coarse, fine


# ---------------------------------------------------------------------------
# CHECKPOINTS
# ---------------------------------------------------------------------------

def guardar_checkpoint(ruta: Path, model, optimizer, epoch: int,
                       train_losses: list, val_losses: list) -> None:
    torch.save({
        "epoch":                epoch,
        "model_state_dict":     model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "train_losses":         train_losses,
        "val_losses":           val_losses,
    }, ruta)


def cargar_checkpoint(ruta: Path, model, optimizer, device):
    ckpt = torch.load(ruta, map_location=device, weights_only=True)
    model.load_state_dict(ckpt["model_state_dict"])
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    return ckpt["epoch"], ckpt["train_losses"], ckpt["val_losses"]


# ---------------------------------------------------------------------------
# BUCLE DE ENTRENAMIENTO
# ---------------------------------------------------------------------------

def train_epoch(model, loader, optimizer, device, w_coarse: float = 0.5) -> float:
    model.train()
    total = 0.0
    for roto, completo in loader:
        roto, completo = roto.to(device), completo.to(device)
        optimizer.zero_grad()
        coarse, fine = model(roto)
        loss = chamfer_distance(fine, completo) + w_coarse * chamfer_distance(coarse, completo)
        loss.backward()
        optimizer.step()
        total += loss.item()
    return total / len(loader)


def val_epoch(model, loader, device, w_coarse: float = 0.5) -> float:
    model.eval()
    total = 0.0
    with torch.no_grad():
        for roto, completo in loader:
            roto, completo = roto.to(device), completo.to(device)
            coarse, fine = model(roto)
            total += (chamfer_distance(fine, completo)
                      + w_coarse * chamfer_distance(coarse, completo)).item()
    return total / len(loader)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Entrenamiento PCN para shape completion E3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--carpetas", nargs="+", default=[
        "Datos/fantastic_breaks/procesado",
        "Datos/sintetico/roturas",
    ], help="Carpetas con pares *_roto.npy / *_completo.npy")
    parser.add_argument("--epochs",       type=int,   default=100)
    parser.add_argument("--batch_size",   type=int,   default=32)
    parser.add_argument("--lr",           type=float, default=1e-4)
    parser.add_argument("--lr_decay",     type=int,   default=40,
                        help="Reducir LR a la mitad cada N épocas")
    parser.add_argument("--n_coarse",     type=int,   default=512,
                        help="Puntos en la salida coarse (fine = n_coarse × 4)")
    parser.add_argument("--checkpoints",  type=str,   default="E3/checkpoints")
    parser.add_argument("--guardar_cada", type=int,   default=5,
                        help="Guardar checkpoint periódico cada N épocas")
    parser.add_argument("--resume",       type=str,   default=None,
                        help="Checkpoint desde el que continuar (ej. E3/checkpoints/best.pt)")
    parser.add_argument("--w_coarse",     type=float, default=0.5,
                        help="Peso de la pérdida coarse (default=0.5; usar 1.0 en v2 para mejorar estructura)")
    parser.add_argument("--device",       type=str,   default=None,
                        help="'cuda' o 'cpu' (None = autodetect)")
    args = parser.parse_args()

    # Device
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")
    if device.type == "cpu":
        print("  Aviso: en CPU un run de 100 épocas puede tardar horas.")
        print("  Prueba con --epochs 2 primero para verificar que funciona.\n")

    # Datos
    train_loader, val_loader, _ = construir_dataloaders(
        carpetas=args.carpetas,
        batch_size=args.batch_size,
    )

    # Modelo
    model = PCN(n_coarse=args.n_coarse).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parámetros entrenables: {n_params:,}")
    print(f"Salida: coarse ({args.n_coarse} pts) + fine ({args.n_coarse * 4} pts)\n")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = StepLR(optimizer, step_size=args.lr_decay, gamma=0.5)

    ckpt_dir = Path(args.checkpoints)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Resume desde checkpoint
    epoch_start = 0
    train_losses, val_losses = [], []
    mejor_val = math.inf

    if args.resume:
        ruta = Path(args.resume)
        epoch_start, train_losses, val_losses = cargar_checkpoint(ruta, model, optimizer, device)
        mejor_val = min(val_losses) if val_losses else math.inf
        print(f"Resumiendo desde {ruta} (última época: {epoch_start})")
        for _ in range(epoch_start):
            scheduler.step()

    # Cabecera de log
    print(f"{'Época':>7}  {'Train':>10}  {'Val':>10}  {'LR':>9}  {'Tiempo':>7}")
    print("-" * 52)

    for epoch in range(epoch_start + 1, args.epochs + 1):
        t0 = time.time()
        loss_train = train_epoch(model, train_loader, optimizer, device, args.w_coarse)
        loss_val   = val_epoch(model, val_loader, device, args.w_coarse)
        scheduler.step()
        elapsed = time.time() - t0

        train_losses.append(loss_train)
        val_losses.append(loss_val)

        lr_now = scheduler.get_last_lr()[0]
        print(f"{epoch:>4}/{args.epochs}  {loss_train:>10.6f}  {loss_val:>10.6f}"
              f"  {lr_now:>9.2e}  {elapsed:>6.1f}s")

        if epoch % args.guardar_cada == 0:
            guardar_checkpoint(
                ckpt_dir / f"epoch_{epoch:03d}.pt",
                model, optimizer, epoch, train_losses, val_losses,
            )

        if loss_val < mejor_val:
            mejor_val = loss_val
            guardar_checkpoint(
                ckpt_dir / "best.pt",
                model, optimizer, epoch, train_losses, val_losses,
            )
            print(f"  → best.pt guardado (val={mejor_val:.6f})")

    print(f"\nFin. Mejor val loss: {mejor_val:.6f}")
    print(f"Checkpoints en: {ckpt_dir}")


if __name__ == "__main__":
    main()
