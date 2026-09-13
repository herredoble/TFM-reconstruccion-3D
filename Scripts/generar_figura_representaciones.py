#!/usr/bin/env python3
"""
Genera una figura comparativa de las 4 representaciones 3D del mismo objeto:
  Malla (wireframe) | Nube de puntos | Vóxel | STL (sólido)

Uso:
    python Scripts/generar_figura_representaciones.py
    python Scripts/generar_figura_representaciones.py --ply Datos/shapenet/limpias/03797390/1038e4eac0e18dcce02ae6d2a21d494a.ply
    python Scripts/generar_figura_representaciones.py --ply <ruta.ply> --salida figura.png

Requiere: trimesh matplotlib numpy  (pip install trimesh matplotlib numpy)
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D           # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import trimesh

# ── Configuración ──────────────────────────────────────────────────────────────
PLY_DEFAULT = r"Datos\shapenet\limpias\03797390\1c3fccb84f1eeb97a3d0a41d6c77ec7c.ply"

ELEV, AZIM   = 28, -45        # ángulo de cámara igual en los 4 paneles
N_PUNTOS     = 2048
RESOLUCION_N = 32              # cuadrícula NxNxN para el vóxel
MAX_CARAS    = 6000            # submuestra de triángulos en los paneles de malla
DPI          = 220
FEATURE_DEG  = 25              # umbral de ángulo diédrico para aristas de contorno (malla)

C_MALLA  = "#1565C0"          # azul
C_NUBE   = "#B71C1C"          # rojo oscuro
C_VOXEL  = "#1B5E20"          # verde oscuro
C_STL    = "#E65100"          # naranja


# ── Carga ──────────────────────────────────────────────────────────────────────

def cargar(ruta: Path) -> trimesh.Trimesh:
    mesh = trimesh.load(str(ruta), force="mesh")
    mesh.vertices -= mesh.vertices.mean(axis=0)
    r = np.linalg.norm(mesh.vertices, axis=1).max()
    if r > 0:
        mesh.vertices /= r
    return mesh


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lim(ax, pts, pad=0.72):
    ax.set_xlim(-pad, pad); ax.set_ylim(-pad, pad); ax.set_zlim(-pad, pad)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=ELEV, azim=AZIM)
    ax.set_axis_off()


def _shading(tris, base_hex, luz=np.array([0.4, 0.3, 1.0])):
    """Devuelve colores RGBA con iluminación difusa para cada triángulo."""
    luz = luz / np.linalg.norm(luz)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nn = np.linalg.norm(n, axis=1, keepdims=True) + 1e-8
    n  = n / nn
    lum = np.clip(np.abs(n @ luz), 0.25, 1.0)   # abs → ambas caras iluminadas
    base = np.array(matplotlib.colors.to_rgb(base_hex))
    rgba = np.column_stack([np.outer(lum, base), np.full(len(tris), 0.93)])
    return np.clip(rgba, 0, 1)


def _depth_sort(faces, verts):
    """Ordena caras de atrás a delante (painter's algorithm) en la vista actual."""
    # Vector de cámara aproximado para la vista (ELEV, AZIM)
    elev_r = np.radians(ELEV); azim_r = np.radians(AZIM)
    cam = np.array([
        np.cos(elev_r) * np.cos(azim_r),
        np.cos(elev_r) * np.sin(azim_r),
        np.sin(elev_r)
    ])
    centroids = verts[faces].mean(axis=1)     # (N, 3)
    depth     = centroids @ cam
    return faces[np.argsort(depth)]           # back-to-front


# ── Panel 1: Malla (wireframe — solo aristas de contorno) ─────────────────────

def dibujar_malla(ax, mesh: trimesh.Trimesh):
    verts = mesh.vertices

    # Aristas de contorno: ángulo diédrico entre caras adyacentes > umbral
    # Esto muestra la estructura de la malla sin las líneas interiores confusas
    try:
        angles = trimesh.graph.face_adjacency_angles(mesh)          # (E_adj,)
        sharp  = angles > np.radians(FEATURE_DEG)
        feat_edges = mesh.face_adjacency_edges[sharp]               # (k, 2)
    except Exception:
        feat_edges = mesh.edges_unique

    # Aristas de borde (sin cara adyacente) — siempre visibles
    try:
        bnd_edges = mesh.edges[trimesh.grouping.group_rows(
            mesh.edges_sorted, require_count=1)]
    except Exception:
        bnd_edges = np.empty((0, 2), dtype=int)

    edges = np.unique(np.vstack([feat_edges, bnd_edges])
                      if len(bnd_edges) else feat_edges, axis=0)

    if len(edges) > 15000:
        idx   = np.random.choice(len(edges), 15000, replace=False)
        edges = edges[idx]

    segs = verts[edges]                # (E, 2, 3)
    lc   = Line3DCollection(segs, colors=C_MALLA, linewidths=0.8, alpha=0.75)
    ax.add_collection3d(lc)

    _lim(ax, verts)
    ax.set_title("Malla (.ply)", fontsize=14, fontweight="bold", pad=4)


# ── Panel 2: Nube de puntos ───────────────────────────────────────────────────

def dibujar_nube(ax, mesh: trimesh.Trimesh):
    pts = np.array(mesh.sample(N_PUNTOS), dtype=np.float32)
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=2.5, c=C_NUBE, alpha=0.75, depthshade=True)
    _lim(ax, pts)
    ax.set_title(f"Nube de puntos (.npy)", fontsize=14, fontweight="bold", pad=4)


# ── Panel 3: Vóxel ────────────────────────────────────────────────────────────

def dibujar_voxel(ax, mesh: trimesh.Trimesh):
    N    = RESOLUCION_N
    pitch = 2.0 / N

    try:
        vox    = mesh.voxelized(pitch=pitch)
        matrix = vox.matrix             # bool (Nx, Ny, Nz)
        origin = vox.transform[:3, 3]
        ix, iy, iz = np.where(matrix)
        pts = np.stack([ix, iy, iz], axis=1).astype(float) * pitch + origin
    except Exception:
        pts_s = np.array(mesh.sample(30000))
        pts_s = np.clip(pts_s, -1 + 1e-5, 1 - 1e-5)
        idx   = ((pts_s + 1) / 2 * N).astype(int)
        idx   = np.clip(idx, 0, N - 1)
        unique = np.unique(idx, axis=0)
        pts   = (unique.astype(float) + 0.5) / N * 2 - 1

    n_ocupados = len(pts)
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=9, c=C_VOXEL, alpha=0.55, marker="s", depthshade=True)
    _lim(ax, pts)
    ax.set_title(f"Vóxel (binvox)", fontsize=14, fontweight="bold", pad=4)


# ── Panel 4: STL (malla sólida con depth-sort) ───────────────────────────────

def dibujar_stl(ax, mesh: trimesh.Trimesh):
    verts = mesh.vertices
    faces = mesh.faces

    if len(faces) > MAX_CARAS:
        idx   = np.random.choice(len(faces), MAX_CARAS, replace=False)
        faces = faces[idx]

    faces = _depth_sort(faces, verts)  # painter's algorithm
    tris  = verts[faces]
    rgba  = _shading(tris, C_STL)

    poly = Poly3DCollection(tris, facecolors=rgba, linewidths=0, alpha=1.0)
    ax.add_collection3d(poly)

    _lim(ax, verts)
    ax.set_title("STL (.stl)", fontsize=14, fontweight="bold", pad=4)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ply",    default=PLY_DEFAULT, help="Ruta al .ply")
    ap.add_argument("--salida", default="figura_representaciones.png")
    ap.add_argument("--seed",   type=int, default=42)
    args = ap.parse_args()

    np.random.seed(args.seed)
    ruta = Path(args.ply)
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}"); return

    print(f"Cargando: {ruta.name} …")
    mesh = cargar(ruta)
    print(f"  Vértices: {len(mesh.vertices):,}  |  Caras: {len(mesh.faces):,}")

    fig = plt.figure(figsize=(18, 6.8), facecolor="white")

    paneles = [
        (dibujar_malla, "Malla (.ply)"),
        (dibujar_nube,  "Nube de puntos (.npy)"),
        (dibujar_voxel, "Vóxel (binvox)"),
        (dibujar_stl,   "STL (.stl)"),
    ]

    for i, (fn, _) in enumerate(paneles):
        ax = fig.add_subplot(1, 4, i + 1, projection="3d")
        fn(ax, mesh)

    fig.suptitle(
        "El mismo objeto en las cuatro representaciones empleadas en el pipeline",
        fontsize=14, fontweight="bold", y=0.98
    )
    plt.tight_layout(pad=0.8)
    plt.subplots_adjust(wspace=0.02, top=0.88, bottom=0.17)

    # Subtítulos descriptivos bajo cada panel (set_xlabel no funciona bien en 3D)
    subtitulos = [
        "Vértices + aristas +\ncaras triangulares",
        f"Solo coordenadas XYZ\n({N_PUNTOS} puntos)",
        f"Rejilla {RESOLUCION_N}³ ocupado/vacío",
        "Triángulos + normales\nSin conectividad — watertight",
    ]
    for i, texto in enumerate(subtitulos):
        fig.text(0.125 + i * 0.25, 0.03, texto,
                 ha="center", va="bottom", fontsize=10, color="#333333")

    salida = Path(args.salida)
    fig.savefig(salida, dpi=DPI, bbox_inches="tight", facecolor="white")
    print(f"Figura guardada en: {salida.resolve()}")
    plt.close(fig)


if __name__ == "__main__":
    main()
