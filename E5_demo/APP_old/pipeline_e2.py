"""
pipeline_e2.py — Etapa 2: 5 fotos de la taza rota -> nube de puntos rota.

Contrato de salida (E2 -> E3), según Documentacion/TFM_11_Contratos_Interfaz.md:
    numpy float32, shape (2048, 3), XYZ en metros, sin normales,
    centrada en origen, escalada a esfera unidad (radio máximo = 1).

Basado en el código de inferencia REAL y ya validado en
`Fantastik_Break_preparacion_Pix2Vox_E2_E3.ipynb` (Celdas 18-21, Drive:
notebooks/), que evaluó Pix2Vox++ contra las 61 tazas rotas de Fantastic
Breaks (ver `evaluacion_pix2vox_pointcloud_vs_roto.csv` /
`evaluacion_pix2vox_voxel_tazas_rotas.csv` en Drive).

Pipeline: 5 imágenes -> Pix2Vox++ -> voxel 32³ -> marching cubes -> malla
-> muestreo de superficie a 2048 puntos -> renormalizar al contrato E2->E3.

⚠️ MUY IMPORTANTE — dos cosas que hay que resolver con el equipo antes de
que esto funcione en producción, no son improvisación mía sino lo que vi
literalmente en el notebook de origen:

1. **Las 5 fotos no son "cualquier 5 fotos".** Pix2Vox++ se entrenó y
   evaluó con exactamente estos 5 ángulos de cámara alrededor del objeto
   (azimuth/elevación, radio de cámara 2.2, focal 50mm):
       vista 0:  az=0°,   el=20°
       vista 5:  az=225°, el=20°
       vista 10: az=90°,  el=40°
       vista 14: az=270°, el=40°
       vista 19: az=270°, el=60°
   Si la app deja que el usuario suba 5 fotos libres desde su móvil, hay
   un desajuste real con la distribución de entrenamiento (esto es un
   tema de E1, no de este módulo, pero condiciona directamente la calidad
   de lo que devuelve E2). Hay que decidir con el grupo: ¿la app le pide al
   usuario que siga una guía visual de 5 ángulos concretos? ¿o hace falta
   reentrenar/fine-tunear con vistas más "libres" tipo smartphone?

2. **`modelo_pix2vox.py` (la clase Pix2VoxPlusPlusA) NO está en el repo de
   GitHub.** Vive como módulo suelto en Drive, en
   `MyDrive/Colab Notebooks/modelo_pix2vox.py`. Para que esta app funcione
   fuera de ese Colab concreto (p.ej. en HF Spaces) hay que mover ese
   fichero al repo (p.ej. a `App/` o a una carpeta `Modelos/`) — de
   momento este módulo asume que es importable vía sys.path, ver
   `ensure_pix2vox_module_available()`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image
from skimage.measure import marching_cubes

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN — confirmada en Fantastik_Break_preparacion_Pix2Vox_E2_E3.ipynb
# ─────────────────────────────────────────────────────────────────────────

TAMANO_IMAGEN = 224
RESOLUCION_VOXEL = 32
MEDIA_IMAGEN = np.array([0.5, 0.5, 0.5], dtype=np.float32)
DESVIACION_IMAGEN = np.array([0.5, 0.5, 0.5], dtype=np.float32)
N_PUNTOS_SALIDA = 2048

# ⚠️ AJUSTAR si el módulo se mueve al repo — de momento sigue en Drive,
# fuera de control de versiones (ver aviso arriba).
RUTA_MODULO_PIX2VOX = Path("/content/drive/MyDrive/Colab Notebooks")

RUTA_BASE_DRIVE = Path("/content/drive/MyDrive/Datos_E2_E3")
RUTA_CHECKPOINTS_E2 = RUTA_BASE_DRIVE / "E2/Pix2Vox++/checkpoints"

# Checkpoint por defecto: el usado en la última evaluación real y
# validada del equipo contra las 61 tazas de Fantastic Breaks (27 ago
# 2026), no un experimento más reciente sin evaluar (exp14 existe, es
# del 25 ago, pero no encontré ninguna comparación exp13 vs exp14 —
# si Rocío/Almu la tienen, cambiar aquí).
DEFAULT_CHECKPOINT_NAME = "exp13_7categorias_5v_finetuning_mejor.pth"


@dataclass
class Pix2VoxConfig:
    checkpoint_name: str = DEFAULT_CHECKPOINT_NAME
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def checkpoint_path(self) -> Path:
        return RUTA_CHECKPOINTS_E2 / self.checkpoint_name


# ─────────────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────────────

def ensure_pix2vox_module_available() -> None:
    """Añade la carpeta de Drive con modelo_pix2vox.py al sys.path."""
    if str(RUTA_MODULO_PIX2VOX) not in sys.path:
        sys.path.append(str(RUTA_MODULO_PIX2VOX))


_MODEL_CACHE: dict[str, tuple] = {}  # checkpoint_name -> (modelo, umbral)


def load_pix2vox_model(config: Pix2VoxConfig | None = None):
    """
    Carga (con caché) Pix2Vox++ + el umbral de binarización guardado en
    el propio checkpoint (mejor_umbral, calibrado en validación).
    """
    config = config or Pix2VoxConfig()
    if config.checkpoint_name in _MODEL_CACHE:
        return _MODEL_CACHE[config.checkpoint_name]

    ensure_pix2vox_module_available()
    from modelo_pix2vox import Pix2VoxPlusPlusA, cargar_checkpoint_finetuning  # type: ignore

    if not config.checkpoint_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el checkpoint Pix2Vox++ en {config.checkpoint_path}."
        )

    modelo = Pix2VoxPlusPlusA(usar_refiner=True, usar_merger=True, usar_pesos_imagenet=False)
    meta = cargar_checkpoint_finetuning(
        modelo=modelo,
        ruta_checkpoint=config.checkpoint_path,
        dispositivo_carga="cpu",
        estricto=True,
    )
    if meta["claves_ausentes"] or meta["claves_inesperadas"]:
        raise RuntimeError(
            f"El checkpoint '{config.checkpoint_name}' no coincide con la arquitectura "
            "de Pix2VoxPlusPlusA (claves ausentes/inesperadas en el state_dict)."
        )

    modelo = modelo.to(config.device)
    modelo.eval()
    umbral = float(meta["mejor_umbral"])

    _MODEL_CACHE[config.checkpoint_name] = (modelo, umbral)
    return modelo, umbral


# ─────────────────────────────────────────────────────────────────────────
# PREPROCESADO DE IMÁGENES (idéntico al notebook de origen)
# ─────────────────────────────────────────────────────────────────────────

def preparar_imagen(imagen_pil: Image.Image, color_fondo=(255, 255, 255)) -> np.ndarray:
    """
    RGBA (o RGB) -> RGB normalizado [-1, 1], 224x224, fondo compuesto en
    blanco. Debe coincidir EXACTAMENTE con el preprocesado usado en
    entrenamiento/evaluación (ver preparar_imagen_pix2vox en el notebook
    de origen) o el checkpoint no generalizará bien.
    """
    rgba = imagen_pil.convert("RGBA")
    fondo = Image.new("RGBA", rgba.size, (*color_fondo, 255))
    compuesta = Image.alpha_composite(fondo, rgba).convert("RGB")

    if compuesta.size != (TAMANO_IMAGEN, TAMANO_IMAGEN):
        compuesta = compuesta.resize(
            (TAMANO_IMAGEN, TAMANO_IMAGEN), resample=Image.Resampling.BILINEAR
        )

    arr = np.asarray(compuesta, dtype=np.float32) / 255.0
    arr = (arr - MEDIA_IMAGEN) / DESVIACION_IMAGEN
    return arr


def imagenes_a_tensor(rutas_o_imagenes: list, device: str) -> torch.Tensor:
    """
    Recibe una lista de 5 imágenes (rutas o PIL.Image, en el orden de las
    5 vistas) y devuelve el tensor (1, 5, 3, 224, 224) que espera el
    modelo.
    """
    if len(rutas_o_imagenes) != 5:
        raise ValueError(
            f"Pix2Vox++ espera exactamente 5 imágenes, recibidas {len(rutas_o_imagenes)}."
        )

    imgs = []
    for item in rutas_o_imagenes:
        img = item if isinstance(item, Image.Image) else Image.open(item)
        imgs.append(preparar_imagen(img))

    tensor = torch.from_numpy(np.stack(imgs)).permute(0, 3, 1, 2).unsqueeze(0).float()
    return tensor.to(device)


# ─────────────────────────────────────────────────────────────────────────
# INFERENCIA: 5 imágenes -> voxel -> malla -> nube de 2048 puntos
# ─────────────────────────────────────────────────────────────────────────

@torch.inference_mode()
def _inferir_voxel(modelo, tensor: torch.Tensor) -> np.ndarray:
    salida = modelo(tensor)
    voxel_prob = salida["volumen_final"].squeeze().detach().cpu().numpy().astype(np.float32)
    forma_esperada = (RESOLUCION_VOXEL,) * 3
    if voxel_prob.shape != forma_esperada:
        raise RuntimeError(f"Shape de voxel inesperado: {voxel_prob.shape}")
    return voxel_prob


def _voxel_binario_a_malla(volumen_binario: np.ndarray) -> trimesh.Trimesh | None:
    volumen = np.asarray(volumen_binario, dtype=bool)
    if volumen.sum() == 0:
        return None

    volumen_pad = np.pad(volumen.astype(np.float32), 1, mode="constant")
    verts, caras, _, _ = marching_cubes(volumen_pad, level=0.5)
    verts = (verts - 1.0 + 0.5) / RESOLUCION_VOXEL
    verts = np.clip(verts, 0.0, 1.0)
    return trimesh.Trimesh(vertices=verts, faces=caras, process=False)


def _normalizar_contrato_e2_e3(puntos_01: np.ndarray) -> np.ndarray:
    """
    Pix2Vox++ trabaja en el cubo [0,1]^3 (convención ShapeNet-render).
    El contrato E2->E3 pide la nube centrada en origen y escalada a
    esfera unidad (radio máximo = 1). Aquí se hace esa conversión.
    """
    centro = puntos_01.mean(axis=0, keepdims=True)
    centrado = puntos_01 - centro
    radio_max = np.linalg.norm(centrado, axis=1).max()
    if radio_max > 0:
        centrado = centrado / radio_max
    return centrado.astype(np.float32)


def fotos_a_nube(
    imagenes: list,
    checkpoint_name: str = DEFAULT_CHECKPOINT_NAME,
    semilla: int = 2026,
) -> np.ndarray:
    """
    Pipeline E2 completo: 5 fotos -> nube de puntos rota (2048, 3),
    normalizada según el contrato E2->E3.

    Parameters
    ----------
    imagenes : list de 5 elementos
        Cada elemento es una ruta a PNG/JPG o un PIL.Image, en el orden
        de las 5 vistas (ver aviso en el docstring del módulo sobre los
        ángulos de cámara esperados).
    checkpoint_name : str
        Nombre del fichero .pth en RUTA_CHECKPOINTS_E2.
    semilla : int
        Semilla para el muestreo de superficie (reproducibilidad).

    Returns
    -------
    np.ndarray, shape (2048, 3), float32
    """
    config = Pix2VoxConfig(checkpoint_name=checkpoint_name)
    modelo, umbral = load_pix2vox_model(config)

    tensor = imagenes_a_tensor(imagenes, config.device)
    voxel_prob = _inferir_voxel(modelo, tensor)
    voxel_bin = voxel_prob >= umbral

    malla = _voxel_binario_a_malla(voxel_bin)
    if malla is None or malla.is_empty or len(malla.faces) == 0:
        raise RuntimeError(
            "Pix2Vox++ no predijo ningún voxel ocupado (o la malla resultante está "
            "vacía) — revisa las fotos de entrada (fondo, encuadre, iluminación)."
        )

    estado_random = np.random.get_state()
    np.random.seed(semilla)
    puntos_01, _ = trimesh.sample.sample_surface(malla, N_PUNTOS_SALIDA)
    np.random.set_state(estado_random)

    return _normalizar_contrato_e2_e3(puntos_01.astype(np.float32))
