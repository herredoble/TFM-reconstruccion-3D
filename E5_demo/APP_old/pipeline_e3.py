"""
pipeline_e3.py — Etapa 3: reparación de la nube de puntos rota con PoinTr.

Contrato de entrada (E2 -> E3), según Documentacion/TFM_11_Contratos_Interfaz.md:
    numpy float32, shape (2048, 3), XYZ en metros, sin normales,
    centrado en origen, escalado a esfera unidad (radio máximo = 1).

Contrato de salida (E3 -> E4):
    numpy float32, shape (2048, 3) — nube COMPLETA (reparada), mismo
    sistema de normalización que la entrada.

Basado en el pipeline de `generar_stl.ipynb` (Drive: notebooks/), que ya
clona PoinTr + el repo del TFM y ejecuta inferencia con el checkpoint
`v5_obj` (CD=0.0306, F=0.2701 — mejor resultado estable a 27 ago 2026).

⚠️ IMPORTANTE (confirmado 28 ago 2026): en Drive, `Raquel/resultados/{VERSION}/`
solo contiene `metricas.json` + `resumen.txt` — el `.pth` del checkpoint
de PoinTr **no está subido a Drive** (probablemente se queda en
`/content/` de Colab, que es efímero). Antes de poder usar este módulo
hace falta que Rocío/Raquel suban el `.pth` de cada versión a Drive, en
la ruta que decidáis (ver DRIVE_E3_ROOT más abajo — es un placeholder).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────

# Checkpoint por defecto: el más completo y mejor confirmado a día de hoy
# (28 ago 2026). Comparado contra el resto de versiones terminadas:
#   v5_obj      CD=0.0306  F=0.2701  (test=41)
#   v5_fb_obj   CD=0.0323  F=0.2548  (test=47)
#   v6_obj_sn   CD=0.0245  F=0.4547  (test=251)  <- gana en ambas métricas
#                                                     y en tamaño de test set
# v7_fb_obj_sn_ft2f (en entrenamiento) podría superarlo, pero aún no tiene
# best.pt de la fase 2 ni evaluación completa. Cambiar aquí en cuanto se
# confirme.
# Caveat: v6_obj_sn se entrenó/evaluó solo con datos sintéticos (Objaverse
# + ShapeNet) — todavía no se ha evaluado contra roturas reales (Fantastic
# Breaks); eso es justo lo que v7 está comprobando ahora mismo.
DEFAULT_CHECKPOINT_VERSION = "v6_obj_sn"

POINTR_REPO_URL = "https://github.com/yuxumin/PoinTr"
POINTR_REPO_DIR = Path("/content/PoinTr")

# Ruta confirmada (28 ago 2026, viendo colab_entrenar_pointr_v7.ipynb):
# el bucle de entrenamiento guarda checkpoints periódicos y "best.pt" con
# shutil.copy2(...) directamente en Drive, en tiempo real durante el
# entrenamiento — no hace falta ninguna acción manual para no perderlos.
DRIVE_E3_ROOT = Path("/content/drive/MyDrive/Datos_E2_E3/E3/Raquel/modelos")


@dataclass
class PoinTrConfig:
    checkpoint_version: str = DEFAULT_CHECKPOINT_VERSION
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def checkpoint_path(self) -> Path:
        # "best.pt" — mismo nombre que usa el propio notebook de
        # entrenamiento (Celda 9) para cargar el modelo evaluado.
        return DRIVE_E3_ROOT / self.checkpoint_version / "best.pt"


# ─────────────────────────────────────────────────────────────────────────
# SETUP (equivalente a la Celda 2 de generar_stl.ipynb)
# ─────────────────────────────────────────────────────────────────────────

def ensure_pointr_available() -> None:
    """Clona PoinTr si hace falta (idempotente, igual que en el notebook)."""
    if not POINTR_REPO_DIR.exists():
        subprocess.run(
            ["git", "clone", POINTR_REPO_URL, str(POINTR_REPO_DIR), "--depth=1", "-q"],
            check=True,
        )


_MODEL_CACHE: dict[str, "torch.nn.Module"] = {}


def load_pointr_model(config: PoinTrConfig | None = None):
    """
    Carga (con caché en memoria) el modelo PoinTr para la versión de
    checkpoint indicada. Se cachea por versión para no recargar pesos en
    cada llamada dentro de la misma sesión de la app.

    Formato del checkpoint confirmado en colab_entrenar_pointr_v7.ipynb
    (28 ago 2026): NO es el checkpoint nativo de PoinTr (builder.load_model),
    sino un dict propio guardado con torch.save() que contiene al menos:
        {
            "epoch": int,
            "model_state_dict": ...,
            "optimizer_state_dict": ...,
            "train_losses": [...], "val_losses": [...],
            "model_cfg": dict(...),   # config del modelo, vía EasyDict
        }
    """
    config = config or PoinTrConfig()
    key = config.checkpoint_version
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    ensure_pointr_available()

    if not config.checkpoint_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el checkpoint PoinTr '{config.checkpoint_version}' en "
            f"{config.checkpoint_path}. Revisa DRIVE_E3_ROOT en pipeline_e3.py, o si "
            "esa versión sigue entrenando, espera a que aparezca 'best.pt'."
        )

    import sys
    sys.path.insert(0, str(POINTR_REPO_DIR))
    from easydict import EasyDict  # type: ignore
    from tools import builder  # type: ignore  # provisto por el repo PoinTr

    ck = torch.load(str(config.checkpoint_path), map_location=config.device, weights_only=False)
    model_cfg = EasyDict(ck["model_cfg"])
    model = builder.model_builder(model_cfg)
    model.load_state_dict(ck["model_state_dict"])
    model = model.to(config.device)
    model.eval()

    _MODEL_CACHE[key] = model
    return model


# ─────────────────────────────────────────────────────────────────────────
# INFERENCIA (equivalente a la Celda 6 de generar_stl.ipynb)
# ─────────────────────────────────────────────────────────────────────────

def reparar_nube(
    nube_rota: np.ndarray,
    checkpoint_version: str = DEFAULT_CHECKPOINT_VERSION,
) -> np.ndarray:
    """
    Repara una nube de puntos rota con PoinTr.

    Parameters
    ----------
    nube_rota : np.ndarray, shape (2048, 3), float32
        Nube incompleta, ya normalizada según el contrato E2->E3
        (centrada en origen, radio máximo = 1).
    checkpoint_version : str
        Nombre de la carpeta de experimento en Drive (p.ej. "v5_obj",
        "v6_obj_sn"). Parametrizable para poder cambiar de modelo sin
        tocar el resto de la app.

    Returns
    -------
    np.ndarray, shape (2048, 3), float32
        Nube completa (reparada), mismo sistema de coordenadas/escala.
    """
    if nube_rota.shape != (2048, 3):
        raise ValueError(
            f"Se esperaba una nube (2048, 3), recibido {nube_rota.shape}. "
            "Revisa la salida de E2 (pipeline_e2.py)."
        )

    config = PoinTrConfig(checkpoint_version=checkpoint_version)
    model = load_pointr_model(config)

    with torch.no_grad():
        entrada = torch.from_numpy(nube_rota).float().unsqueeze(0).to(config.device)
        # PoinTr devuelve típicamente una lista/tupla de salidas jerárquicas;
        # se toma la de mayor resolución (última). Ajustar si vuestro
        # checkpoint concreto expone otra interfaz.
        salida = model(entrada)
        nube_completa = salida[-1] if isinstance(salida, (list, tuple)) else salida
        nube_completa = nube_completa.squeeze(0).cpu().numpy().astype(np.float32)

    return nube_completa


def guardar_nube(nube: np.ndarray, ruta_salida: str | os.PathLike) -> None:
    """Guarda la nube reparada como .npy (formato del contrato E3->E4)."""
    np.save(ruta_salida, nube.astype(np.float32))
