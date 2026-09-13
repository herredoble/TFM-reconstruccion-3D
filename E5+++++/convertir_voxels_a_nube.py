"""
Scripts/convertir_voxels_a_nube.py
────────────────────────────────────────────────────────────────────────────────
Conversión E2 → E3: voxel grid (Pix2Vox++) → nube de puntos (2048, 3)

ENTRADA  : grid de vóxeles numpy float32 shape (D, H, W) o (1, D, H, W)
           producido por Pix2Vox++, tipicamente 32×32×32
SALIDA   : nube de puntos float32 shape (2048, 3)
           centrada en origen, escala esfera unidad (radio máximo = 1)
           lista para pasar directamente a PoinTr / PCN / TopNet

USO DESDE LÍNEA DE COMANDOS:
  python Scripts/convertir_voxels_a_nube.py ruta_voxels.npy --salida nube.npy

USO DESDE CÓDIGO:
  from Scripts.convertir_voxels_a_nube import voxels_a_nube
  nube = voxels_a_nube(grid_32x32x32)   # devuelve (2048, 3) float32
"""

import numpy as np
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# Función principal
# ──────────────────────────────────────────────────────────────────────────────

def voxels_a_nube(
    voxels: np.ndarray,
    n_puntos: int = 2048,
    umbral: float = 0.5,
    semilla: int = 42,
    metodo_submuestreo: str = "fps",     # "fps" | "random"
    metodo_superficie: str = "superficie",  # "superficie" | "ocupados"
) -> np.ndarray:
    """
    Convierte un grid de vóxeles a una nube de puntos (n_puntos, 3).

    Parámetros
    ----------
    voxels : ndarray float32
        Grid de vóxeles, shape (D, H, W) o (1, D, H, W) o (B, 1, D, H, W).
        Valores en [0, 1] (probabilidad de ocupación) o binarios.
    n_puntos : int
        Número de puntos de salida. Por defecto 2048 (estándar E3).
    umbral : float
        Umbral de binarización: voxel ocupado si valor > umbral.
    semilla : int
        Semilla para reproducibilidad en el submuestreo aleatorio.
    metodo_submuestreo : str
        "fps"    → Furthest Point Sampling (más uniforme, más lento).
        "random" → muestreo aleatorio (más rápido).
    metodo_superficie : str
        "superficie" → solo vóxeles con al menos un vecino vacío (frontera).
        "ocupados"   → todos los vóxeles ocupados (incluye interior).

    Devuelve
    --------
    ndarray float32, shape (n_puntos, 3)
        Coordenadas XYZ normalizadas: centradas en origen, radio máximo = 1.

    Notas de diseño
    ---------------
    Un grid 32×32×32 tiene resolución espacial 1/32 ≈ 0.031 por celda.
    Con un objeto típico ocupando ~30% del volumen (~9.800 vóxeles), el
    número de puntos de superficie es ~3.000-6.000, suficiente para 2048.
    Con objetos muy finos (asa de taza) puede haber pocos puntos de frontera;
    en ese caso el método cae a "ocupados" automáticamente.
    """
    rng = np.random.default_rng(semilla)

    # ── 1. Normalizar forma ────────────────────────────────────────────────────
    v = np.asarray(voxels, dtype=np.float32)
    while v.ndim > 3:
        v = v[0]                 # quitar dimensiones de batch/canal

    D, H, W = v.shape

    # ── 2. Binarizar ──────────────────────────────────────────────────────────
    ocupado = v > umbral         # bool (D, H, W)

    # ── 3. Extraer puntos ─────────────────────────────────────────────────────
    if metodo_superficie == "superficie":
        frontera = _mascara_superficie(ocupado)
        pts = _centros_voxel(frontera, D, H, W)
        if len(pts) < n_puntos // 4:
            # muy pocos puntos de frontera → caer a todos los ocupados
            pts = _centros_voxel(ocupado, D, H, W)
    else:
        pts = _centros_voxel(ocupado, D, H, W)

    if len(pts) == 0:
        raise ValueError(
            f"El grid de vóxeles está vacío (umbral={umbral}). "
            "Verifica que la salida de Pix2Vox++ sea correcta."
        )

    # ── 4. Añadir jitter submilimétrico para evitar puntos coplanares ─────────
    # Desplazamiento aleatorio dentro de la celda (±0.4 del tamaño de celda)
    cell_size = 1.0 / max(D, H, W)
    jitter = rng.uniform(-0.4 * cell_size, 0.4 * cell_size, pts.shape)
    pts = pts + jitter.astype(np.float32)

    # ── 5. Submuestrear a n_puntos ────────────────────────────────────────────
    if len(pts) > n_puntos:
        if metodo_submuestreo == "fps":
            idx = _fps(pts, n_puntos, rng)
        else:
            idx = rng.choice(len(pts), n_puntos, replace=False)
        pts = pts[idx]
    elif len(pts) < n_puntos:
        # Repetir puntos con jitter adicional para llegar a n_puntos
        n_extra = n_puntos - len(pts)
        idx_extra = rng.choice(len(pts), n_extra, replace=True)
        extra = pts[idx_extra] + rng.uniform(
            -cell_size, cell_size, (n_extra, 3)
        ).astype(np.float32)
        pts = np.concatenate([pts, extra], axis=0)

    # ── 6. Normalizar: centrar + escala esfera unidad ─────────────────────────
    centroide = pts.mean(axis=0)
    pts = pts - centroide
    radio_max = float(np.linalg.norm(pts, axis=1).max())
    if radio_max > 1e-8:
        pts = pts / radio_max

    return pts.astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────────
# Funciones auxiliares internas
# ──────────────────────────────────────────────────────────────────────────────

def _centros_voxel(mascara: np.ndarray, D: int, H: int, W: int) -> np.ndarray:
    """Coordenadas normalizadas del centro de cada vóxel marcado como True."""
    zz, yy, xx = np.where(mascara)
    if len(zz) == 0:
        return np.empty((0, 3), dtype=np.float32)
    # Normalizar a [-1, 1] dentro del grid
    x = (xx.astype(np.float32) + 0.5) / W * 2 - 1
    y = (yy.astype(np.float32) + 0.5) / H * 2 - 1
    z = (zz.astype(np.float32) + 0.5) / D * 2 - 1
    return np.stack([x, y, z], axis=1)


def _mascara_superficie(ocupado: np.ndarray) -> np.ndarray:
    """Vóxeles ocupados que tienen al menos un vecino (6-conexo) vacío."""
    from scipy.ndimage import binary_dilation
    kernel = np.array([[[0,0,0],[0,1,0],[0,0,0]],
                       [[0,1,0],[1,1,1],[0,1,0]],
                       [[0,0,0],[0,1,0],[0,0,0]]], dtype=bool)
    dilatado = binary_dilation(~ocupado, structure=kernel)
    return ocupado & dilatado


def _fps(pts: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Furthest Point Sampling — selecciona n índices lo más separados posible."""
    N = len(pts)
    idx = np.zeros(n, dtype=np.int64)
    dist = np.full(N, np.inf, dtype=np.float32)
    actual = int(rng.integers(0, N))
    for i in range(n):
        idx[i] = actual
        d = np.sum((pts - pts[actual]) ** 2, axis=1)
        dist = np.minimum(dist, d)
        actual = int(np.argmax(dist))
    return idx


# ──────────────────────────────────────────────────────────────────────────────
# Función de diagnóstico
# ──────────────────────────────────────────────────────────────────────────────

def diagnosticar_voxels(voxels: np.ndarray, umbral: float = 0.5) -> dict:
    """Estadísticas de un grid de vóxeles para detectar problemas antes de convertir."""
    v = np.asarray(voxels, dtype=np.float32)
    while v.ndim > 3:
        v = v[0]
    D, H, W = v.shape
    ocupados = int((v > umbral).sum())
    total = D * H * W
    pct = 100 * ocupados / total
    frontera = _mascara_superficie(v > umbral)
    n_frontera = int(frontera.sum())
    return {
        "forma_grid": (D, H, W),
        "voxeles_totales": total,
        "voxeles_ocupados": ocupados,
        "porcentaje_ocupado": round(pct, 2),
        "voxeles_superficie": n_frontera,
        "resolucion_celda": round(1.0 / max(D, H, W), 4),
        "suficiente_para_2048": n_frontera >= 512,
        "advertencias": [
            f"Solo {n_frontera} vóxeles de superficie — se usarán todos los ocupados"
            if n_frontera < 512 else "",
            f"Grid muy escaso ({pct:.1f}% ocupado)" if pct < 5 else "",
            f"Grid casi lleno ({pct:.1f}% ocupado) — ¿se aplicó el umbral correcto?"
            if pct > 80 else "",
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convierte vóxeles de Pix2Vox++ a nube de puntos (2048,3) para E3."
    )
    parser.add_argument("entrada", help="Ruta al .npy de vóxeles (salida de E2)")
    parser.add_argument("--salida", default=None, help="Ruta de salida .npy (default: misma carpeta, _nube.npy)")
    parser.add_argument("--n_puntos", type=int, default=2048)
    parser.add_argument("--umbral", type=float, default=0.5)
    parser.add_argument("--metodo", choices=["fps", "random"], default="fps")
    parser.add_argument("--diagnostico", action="store_true", help="Solo mostrar estadísticas, no convertir")
    args = parser.parse_args()

    ruta = Path(args.entrada)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encuentra: {ruta}")

    voxels = np.load(str(ruta))
    print(f"Cargado: {ruta}  shape={voxels.shape}  dtype={voxels.dtype}")

    diag = diagnosticar_voxels(voxels, args.umbral)
    print("\n── Diagnóstico ───────────────────────────────")
    for k, v in diag.items():
        if k != "advertencias":
            print(f"  {k:30s}: {v}")
    for w in diag["advertencias"]:
        if w:
            print(f"  ⚠️  {w}")

    if args.diagnostico:
        raise SystemExit(0)

    nube = voxels_a_nube(voxels, n_puntos=args.n_puntos, umbral=args.umbral,
                         metodo_submuestreo=args.metodo)
    print(f"\nNube generada: shape={nube.shape}  dtype={nube.dtype}")
    print(f"  rango X: [{nube[:,0].min():.3f}, {nube[:,0].max():.3f}]")
    print(f"  rango Y: [{nube[:,1].min():.3f}, {nube[:,1].max():.3f}]")
    print(f"  rango Z: [{nube[:,2].min():.3f}, {nube[:,2].max():.3f}]")
    print(f"  radio máx: {float(np.linalg.norm(nube, axis=1).max()):.4f}  (debe ser ≈1.0)")

    salida = Path(args.salida) if args.salida else ruta.parent / (ruta.stem + "_nube.npy")
    np.save(str(salida), nube)
    print(f"\nGuardado: {salida}")
