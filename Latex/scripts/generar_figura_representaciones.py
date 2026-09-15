"""
Genera figura_representaciones.png para la memoria LaTeX.

Muestra la misma taza en las 4 representaciones del pipeline:
  malla (.ply), nube de puntos (.npy), vóxel (binvox) y STL (.stl)

Uso en Colab:
    !python generar_figura_representaciones.py \
        --ply   /content/drive/MyDrive/.../taza.ply \
        --npy   /content/drive/MyDrive/.../taza_rota.npy \
        --binvox /content/drive/MyDrive/.../taza.binvox \
        --stl   /content/drive/MyDrive/.../taza.stl \
        --out   figura_representaciones.png

Dependencias:  pip install trimesh numpy matplotlib
Para binvox:   pip install binvox-rw
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ── argumentos ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ply",    required=True)
parser.add_argument("--npy",    required=True)
parser.add_argument("--binvox", required=True)
parser.add_argument("--stl",    required=True)
parser.add_argument("--out",    default="figura_representaciones.png")
args = parser.parse_args()

# ── carga de datos ─────────────────────────────────────────────────────────────
import trimesh

mesh_ply = trimesh.load(args.ply, force="mesh")
mesh_stl = trimesh.load(args.stl, force="mesh")
nube     = np.load(args.npy)           # (N, 3)

import binvox_rw
with open(args.binvox, "rb") as f:
    vox = binvox_rw.read_as_3d_array(f)
voxel_data = vox.data                 # bool array (D, D, D)

# ── figura ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 5.5), facecolor="white")
fig.suptitle(
    "El mismo objeto en las cuatro representaciones empleadas en el pipeline",
    fontsize=15, fontweight="bold", y=1.01
)

gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.05)

ELEV, AZIM = 20, -60
TITLES = [
    ("Malla (.ply)",          "#3a7abf"),
    ("Nube de puntos (.npy)", "#d94f3d"),
    ("Vóxel (binvox)",        "#3aab6a"),
    ("STL (.stl)",            "#c07a30"),
]

# ── panel 1: malla PLY ────────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0], projection="3d")
verts = mesh_ply.vertices
faces = mesh_ply.faces
poly  = Poly3DCollection(verts[faces], alpha=0.25,
                          facecolor=TITLES[0][1], edgecolor="none")
ax1.add_collection3d(poly)
ax1.auto_scale_xyz(verts[:, 0], verts[:, 1], verts[:, 2])

# ── panel 2: nube de puntos ───────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1], projection="3d")
# submuestrear si es muy densa
pts = nube if len(nube) <= 2048 else nube[np.random.choice(len(nube), 2048, replace=False)]
ax2.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
            s=2, c=TITLES[1][1], alpha=0.7, depthshade=True)

# ── panel 3: vóxel ────────────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[2], projection="3d")
ax3.voxels(voxel_data, facecolors=TITLES[2][1], edgecolors="none", alpha=0.6)

# ── panel 4: STL ─────────────────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[3], projection="3d")
verts_s = mesh_stl.vertices
faces_s = mesh_stl.faces
poly_s  = Poly3DCollection(verts_s[faces_s], alpha=0.85,
                            facecolor=TITLES[3][1], edgecolor="none")
ax4.add_collection3d(poly_s)
ax4.auto_scale_xyz(verts_s[:, 0], verts_s[:, 1], verts_s[:, 2])

# ── estilo común ──────────────────────────────────────────────────────────────
for ax, (title, color) in zip([ax1, ax2, ax3, ax4], TITLES):
    ax.set_title(title, fontsize=13, fontweight="bold", color=color, pad=8)
    ax.set_xlabel("X", fontsize=9, labelpad=2)
    ax.set_ylabel("Y", fontsize=9, labelpad=2)
    ax.set_zlabel("Z", fontsize=9, labelpad=2)
    ax.tick_params(labelsize=7)
    ax.view_init(elev=ELEV, azim=AZIM)
    ax.set_facecolor("#f8f8f8")
    ax.grid(True, linewidth=0.4, alpha=0.5)

plt.tight_layout()
plt.savefig(args.out, dpi=200, bbox_inches="tight", facecolor="white")
print(f"Guardado: {args.out}")
