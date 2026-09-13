# -*- coding: utf-8 -*-
"""
E3/evaluate.py — Evaluación del modelo PCN en el conjunto de test.

MÉTRICAS
  - Chamfer Distance (CD-L1): distancia media entre nubes predichas y GT.
    Nota: el val-loss del entrenamiento era CD(fine) + 0.5·CD(coarse).
    Aquí se reporta solo CD(fine), que será más bajo — es el número real.
  - F-Score@τ: precisión-recall con umbral de distancia τ (por defecto τ=0.01).
    τ=0.01 sobre la esfera unidad equivale a tolerar 1% de la escala del objeto.

USO (siempre desde la raíz del repo, c:/EDF/TFM)
  python -m E3.evaluate                          # best.pt, 8 figuras
  python -m E3.evaluate --visualizar 0           # solo métricas, sin figuras
  python -m E3.evaluate --checkpoint E3/checkpoints/epoch_100.pt
  python -m E3.evaluate --tau 0.02               # F-Score con umbral más permisivo

⚠️  ANTES DE EJECUTAR: descarga best.pt desde Drive → E3/checkpoints/best.pt

SALIDAS
  E3/resultados/metricas.csv     métricas por muestra (idx, CD, F-Score)
  E3/resultados/resumen.txt      estadísticos globales
  E3/resultados/figura_NNN.png   4 paneles por figura: roto | GT | pred | overlay
"""

import argparse
import csv
from pathlib import Path

import numpy as np
import torch

from E3.dataset import construir_dataloaders
from E3.train import PCN, chamfer_distance


# ---------------------------------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------------------------------

def fscore(pred: torch.Tensor, gt: torch.Tensor, tau: float) -> torch.Tensor:
    """F-Score@τ — mide qué fracción de puntos está dentro de distancia τ.

    Precisión = fracción de puntos predichos con un punto GT a menos de τ.
    Recall    = fracción de puntos GT con un punto predicho a menos de τ.
    F-Score   = media armónica de precisión y recall.

    pred, gt: (B, N, 3)
    Devuelve: tensor (B,) con el F-Score de cada muestra del batch.
    """
    dist = torch.cdist(pred, gt, p=2)                              # (B, N_pred, N_gt)
    precision = (dist.min(dim=2).values < tau).float().mean(dim=1) # (B,)
    recall    = (dist.min(dim=1).values < tau).float().mean(dim=1) # (B,)
    denom = precision + recall
    return torch.where(denom > 0,
                       2 * precision * recall / denom,
                       torch.zeros_like(denom))


# ---------------------------------------------------------------------------
# VISUALIZACIÓN
# ---------------------------------------------------------------------------

def _configurar_panel(ax, pts: np.ndarray, titulo: str, color: str, alpha: float = 0.7):
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               c=color, s=2.5, alpha=alpha, linewidths=0)
    ax.set_title(titulo, fontsize=10, pad=6)
    ax.set_axis_off()
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=20, azim=45)  # ángulo fijo para que los 4 paneles sean comparables


def visualizar_cuarteto(
    roto: np.ndarray,
    gt: np.ndarray,
    pred: np.ndarray,
    titulo: str,
    ruta_salida: Path,
) -> None:
    """Guarda una figura con 4 paneles:
      1. Entrada rota (lo que ve el modelo)
      2. GT completa (lo que debería predecir)
      3. Predicción del modelo
      4. Overlay: GT (gris, transparente) + predicción (naranja) — muestra los errores
    """
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(20, 5))
    fig.suptitle(titulo, fontsize=11, y=1.01)

    paneles = [
        (roto, "Entrada (rota)",      "#4C72B0", 0.7),  # azul
        (gt,   "GT (completa)",        "#55A868", 0.7),  # verde
        (pred, "Predicción",           "#C44E52", 0.7),  # rojo
    ]
    for i, (pts, etiqueta, color, alpha) in enumerate(paneles, 1):
        ax = fig.add_subplot(1, 4, i, projection="3d")
        _configurar_panel(ax, pts, etiqueta, color, alpha)

    # Panel 4: overlay GT (gris, semi-transparente) + predicción (naranja)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    ax4.scatter(gt[:, 0],   gt[:, 1],   gt[:, 2],
                c="#AAAAAA", s=2.5, alpha=0.25, linewidths=0, label="GT")
    ax4.scatter(pred[:, 0], pred[:, 1], pred[:, 2],
                c="#DD8452", s=2.5, alpha=0.8,  linewidths=0, label="Pred")
    ax4.set_title("Overlay GT (gris) + Pred (naranja)", fontsize=10, pad=6)
    ax4.set_axis_off()
    ax4.set_xlim(-1, 1); ax4.set_ylim(-1, 1); ax4.set_zlim(-1, 1)
    ax4.set_box_aspect([1, 1, 1])
    ax4.view_init(elev=20, azim=45)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# EVALUACIÓN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluación del modelo PCN en test set",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--checkpoint",  default="E3/checkpoints/best.pt",
                        help="Ruta al .pt a evaluar (descárgalo de Drive si no está)")
    # ⚠️ Las carpetas y semilla DEBEN coincidir con las usadas en train.py
    # para que el test set sea el mismo y las métricas sean válidas.
    parser.add_argument("--carpetas", nargs="+", default=[
        "Datos/fantastic_breaks/procesado",
        "Datos/sintetico/roturas",
    ])
    parser.add_argument("--batch_size", type=int,   default=32)
    parser.add_argument("--tau",        type=float, default=0.01,
                        help="Umbral de distancia para F-Score (en unidades esfera unidad)")
    parser.add_argument("--visualizar", type=int,   default=8,
                        help="Número de figuras a guardar (mejores + peores por CD). 0 = ninguna")
    parser.add_argument("--salida",     default="E3/resultados")
    parser.add_argument("--device",     default=None)
    args = parser.parse_args()

    # Verificar que el checkpoint existe antes de empezar
    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el checkpoint: {ckpt_path}\n"
            "Descárgalo de Drive → E3/checkpoints/best.pt"
        )

    # Device
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"Dispositivo: {device}")

    # Datos — test split con los mismos parámetros que train.py (semilla=42, split 80/10/10)
    _, _, test_loader = construir_dataloaders(
        carpetas=args.carpetas,
        batch_size=args.batch_size,
        augmentar=False,
    )
    n_test = len(test_loader.dataset)
    print(f"Muestras en test: {n_test}")

    # Modelo
    model = PCN().to(device)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=True)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print(f"Checkpoint: {ckpt_path}  (época {ckpt['epoch']})\n")

    # Evaluación por muestra
    resultados = []
    muestras   = []  # (roto, gt, pred, cd) para las visualizaciones

    with torch.no_grad():
        for roto_batch, gt_batch in test_loader:
            roto_batch = roto_batch.to(device)
            gt_batch   = gt_batch.to(device)
            _, fine_batch = model(roto_batch)

            fs_batch = fscore(fine_batch, gt_batch, tau=args.tau)

            for j in range(roto_batch.size(0)):
                p = fine_batch[j:j+1]
                g = gt_batch[j:j+1]
                cd = chamfer_distance(p, g).item()
                fs = fs_batch[j].item()
                idx = len(resultados)
                resultados.append({"idx": idx, "cd": cd, f"fscore_t{args.tau}": fs})
                if args.visualizar > 0:
                    muestras.append((
                        roto_batch[j].cpu().numpy(),
                        gt_batch[j].cpu().numpy(),
                        fine_batch[j].cpu().numpy(),
                        cd, fs,
                    ))

    # Guardar CSV
    salida_dir = Path(args.salida)
    salida_dir.mkdir(parents=True, exist_ok=True)

    csv_path = salida_dir / "metricas.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)

    # Resumen global
    cds = np.array([r["cd"] for r in resultados])
    fss = np.array([r[f"fscore_t{args.tau}"] for r in resultados])
    resumen = (
        f"=== Evaluación E3 — {len(resultados)} muestras ===\n"
        f"Checkpoint : {ckpt_path}  (época {ckpt['epoch']})\n"
        f"Nota       : val-loss del entrenamiento = CD(fine) + 0.5·CD(coarse).\n"
        f"             Aquí se reporta solo CD(fine) → número más bajo, es correcto.\n\n"
        f"Chamfer Distance (CD-L1):\n"
        f"  media    : {cds.mean():.6f}\n"
        f"  mediana  : {np.median(cds):.6f}\n"
        f"  std      : {cds.std():.6f}\n"
        f"  mejor    : {cds.min():.6f}  (muestra {cds.argmin()})\n"
        f"  peor     : {cds.max():.6f}  (muestra {cds.argmax()})\n\n"
        f"F-Score @ τ={args.tau}:\n"
        f"  media    : {fss.mean():.4f}\n"
        f"  mediana  : {np.median(fss):.4f}\n"
        f"  std      : {fss.std():.4f}\n"
        f"  mejor    : {fss.max():.4f}  (muestra {fss.argmax()})\n"
        f"  peor     : {fss.min():.4f}  (muestra {fss.argmin()})\n"
    )
    print(resumen)
    (salida_dir / "resumen.txt").write_text(resumen, encoding="utf-8")
    print(f"CSV guardado: {csv_path}")

    # Visualizaciones: mejores N/2 y peores N/2 por CD
    if args.visualizar > 0 and muestras:
        n_cada = max(1, args.visualizar // 2)
        orden_cd = np.argsort(cds)
        indices_viz = list(orden_cd[:n_cada]) + list(orden_cd[-n_cada:])
        etiquetas   = (["mejor"] * n_cada) + ["peor"] * n_cada

        print(f"\nGenerando {len(indices_viz)} figuras ({n_cada} mejores + {n_cada} peores)...")
        for rank, (idx_m, etiq) in enumerate(zip(indices_viz, etiquetas), 1):
            r, g, p, cd, fs = muestras[idx_m]
            titulo = f"Muestra {idx_m} [{etiq}] — CD={cd:.5f}  F-Score={fs:.3f}"
            ruta = salida_dir / f"figura_{rank:03d}_{etiq}_{idx_m}.png"
            visualizar_cuarteto(r, g, p, titulo, ruta)
            print(f"  {ruta.name}")

    print(f"\nTodo guardado en: {salida_dir}/")


if __name__ == "__main__":
    main()
