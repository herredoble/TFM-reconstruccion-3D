
"""
pipeline_e4.py — Etapa 4: nube de puntos reparada -> STL imprimible.

Contrato de entrada (E3 -> E4), según Documentacion/TFM_11_Contratos_Interfaz.md:
    malla completa .obj/.ply, o en nuestro caso la nube de puntos completa
    (2048, 3) de la que se reconstruye la malla aquí mismo.

Contrato de salida (E4 -> E5):
    .STL watertight, escala física en mm, + report.json con:
    watertight (bool), nº de errores reparados, volumen.

⚠️ CAMBIO DE ENFOQUE (28 ago 2026): la primera versión de este módulo usaba
Poisson surface reconstruction de Open3D, tal como en `generar_stl.ipynb`.
Al probarlo en Colab dio:
    ERROR: No matching distribution found for open3d
Open3D no publica wheels para la versión de Python de ese runtime (ver
aviso ya existente en CLAUDE.md: "trimesh, no open3d — no tiene build").
No es un problema puntual de una máquina, así que en vez de pedir al
grupo que fije una versión de Python distinta solo para poder instalar
Open3D, este módulo se ha reescrito sin esa dependencia:

    nube de puntos -> función de distancia sin signo (KDTree) sobre una
    rejilla 3D -> superficie isométrica con marching cubes (scikit-image)
    -> trimesh para limpieza/watertight/exportación.

No es Poisson (no usa normales orientadas), es una reconstrucción por
"unsigned distance function" — más simple, sin dependencias problemáticas,
y con calidad razonable para nubes ya densas y limpias como las que salen
de PoinTr (2048 puntos, sin ruido). Si la calidad no basta, alternativas a
valorar sin salir de trimesh/scipy: `alphashape`, o subir la resolución de
la rejilla (`grid_resolution`).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

import trimesh


# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    # Resolución de la rejilla 3D sobre la que se evalúa la función de
    # distancia. Más alto = más detalle pero más lento (coste ~ N^3).
    # 96 es un buen punto de partida para 2048 puntos de entrada.
    grid_resolution: int = 96

    # El nivel (isovalor) de la superficie se fija como un múltiplo de la
    # separación mediana entre puntos vecinos de la propia nube, para que
    # se adapte automáticamente a la densidad real de cada nube en vez de
    # usar una distancia fija en unidades normalizadas.
    factor_nivel: float = 1.4

    # Margen extra alrededor del bounding box de la nube (evita cortar la
    # superficie reconstruida justo en el borde de la rejilla).
    margen_relativo: float = 0.15

    # Escala física de salida. El contrato E2->E3 normaliza a esfera
    # unidad (radio máximo = 1); el contrato E4->E5 pide mm reales. El
    # tamaño físico real no se puede inferir de la nube normalizada sin
    # más contexto (p.ej. una referencia de escala en la foto) — AJUSTAR
    # según decisión de equipo / lo que introduzca el usuario en la app.
    escala_salida_mm: float = 100.0


# ─────────────────────────────────────────────────────────────────────────
# RECONSTRUCCIÓN DE MALLA: unsigned distance function + marching cubes
# ─────────────────────────────────────────────────────────────────────────

def nube_a_malla(nube: np.ndarray, config: Config | None = None) -> trimesh.Trimesh:
    """
    Reconstruye una malla a partir de una nube de puntos completa (2048, 3)
    evaluando la distancia sin signo a la nube sobre una rejilla 3D y
    extrayendo la isosuperficie con marching cubes.
    """
    config = config or Config()
    puntos = nube.astype(np.float64)

    arbol = cKDTree(puntos)

    # Separación típica entre puntos vecinos -> define el nivel de la
    # isosuperficie (a qué distancia de los puntos "está la superficie").
    distancias_vecino, _ = arbol.query(puntos, k=2)
    separacion_mediana = float(np.median(distancias_vecino[:, 1]))
    nivel = separacion_mediana * config.factor_nivel

    # Rejilla 3D con margen alrededor del bounding box de la nube.
    minimos = puntos.min(axis=0)
    maximos = puntos.max(axis=0)
    centro = (minimos + maximos) / 2
    radio = float(np.max(maximos - minimos)) / 2
    margen = radio * config.margen_relativo
    minimos_grid = centro - radio - margen
    maximos_grid = centro + radio + margen

    resolucion = config.grid_resolution
    ejes = [np.linspace(minimos_grid[i], maximos_grid[i], resolucion) for i in range(3)]
    gx, gy, gz = np.meshgrid(*ejes, indexing="ij")
    puntos_grid = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    distancias, _ = arbol.query(puntos_grid, k=1)
    volumen_distancias = distancias.reshape(resolucion, resolucion, resolucion)

    if volumen_distancias.min() >= nivel:
        raise RuntimeError(
            "No se encontró ninguna isosuperficie al nivel calculado "
            f"({nivel:.4f}) — la nube de puntos puede estar vacía o ser "
            "degenerada. Revisa la salida de E3 (reparar_nube)."
        )

    verts_grid, caras, _, _ = marching_cubes(volumen_distancias, level=nivel)

    # Reescalar de índices de rejilla a coordenadas reales de la nube.
    espaciado = (maximos_grid - minimos_grid) / (resolucion - 1)
    verts_reales = verts_grid * espaciado + minimos_grid

    malla = trimesh.Trimesh(vertices=verts_reales, faces=caras, process=True)
    return malla


# ─────────────────────────────────────────────────────────────────────────
# LIMPIEZA + EXPORTAR STL WATERTIGHT
# ─────────────────────────────────────────────────────────────────────────

def limpiar_y_exportar_stl(
    malla: trimesh.Trimesh,
    ruta_salida: str | os.PathLike,
    config: Config | None = None,
) -> dict:
    """
    Limpia la malla (componente conexa más grande, repara huecos/normales)
    y la exporta como STL watertight, en mm.

    Returns
    -------
    dict — mismo contenido que se escribe en report.json (contrato E4->E5):
        {"watertight": bool, "errores_reparados": int, "volumen_mm3": float}
    """
    config = config or Config()

    # Quedarse solo con la componente conexa más grande (elimina "islas"
    # sueltas que a veces genera la isosuperficie en zonas ruidosas).
    componentes = malla.split(only_watertight=False)
    if len(componentes) > 1:
        malla = max(componentes, key=lambda m: len(m.faces))

    errores_reparados = 0
    if not malla.is_watertight:
        antes = malla.is_watertight
        trimesh.repair.fill_holes(malla)
        trimesh.repair.fix_normals(malla)
        trimesh.repair.fix_winding(malla)
        errores_reparados = 1 if (antes != malla.is_watertight) else 0

    # Escalar a la escala física de salida (mm). La nube de entrada está
    # normalizada a esfera unidad (radio máximo = 1); se reescala a
    # `escala_salida_mm` de tamaño de referencia.
    escala_actual = malla.bounding_sphere.primitive.radius
    if escala_actual > 0:
        factor = config.escala_salida_mm / (2 * escala_actual)
        malla.apply_scale(factor)

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    malla.export(ruta_salida)

    report = {
        "watertight": bool(malla.is_watertight),
        "errores_reparados": errores_reparados,
        "volumen_mm3": float(malla.volume) if malla.is_watertight else None,
    }

    ruta_report = ruta_salida.with_suffix(".report.json")
    with open(ruta_report, "w") as f:
        json.dump(report, f, indent=2)

    return report


# ─────────────────────────────────────────────────────────────────────────
# FUNCIÓN DE ALTO NIVEL — nube reparada -> STL + report
# ─────────────────────────────────────────────────────────────────────────

def nube_a_stl(
    nube_completa: np.ndarray,
    ruta_salida: str | os.PathLike,
    config: Config | None = None,
) -> dict:
    """Pipeline E3->E4 completo: nube reparada -> malla -> STL watertight."""
    config = config or Config()
    malla = nube_a_malla(nube_completa, config)
    return limpiar_y_exportar_stl(malla, ruta_salida, config)

