"""
Genera figura_representaciones.png para la memoria LaTeX.

Muestra la misma taza en las 4 representaciones del pipeline:
  malla (.ply), nube de puntos (.npy), vóxel (generado desde .ply) y STL (.stl)

Uso en Colab:
    !python generar_figura_representaciones.py \
        --ply  /content/drive/MyDrive/.../objeto.ply \
        --npy  /content/drive/MyDrive/.../objeto_roto.npy \
        --stl  /content/drive/MyDrive/.../objeto.stl \
        --out  figura_representaciones.png

Dependencias:  pip install trimesh numpy matplotlib scipy
El vóxel se genera automáticamente desde el .ply (no necesita .binvox).
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

parser = argparse.ArgumentParser()
parser.add_argument("--ply", required=True)
parser.add_argument("--npy", required=True)
parser.add_argument("--stl", required=True)
parser.add_argument("--out", default="figura_representaciones.png")
parser.add_argument("--voxel_pitch", type=float, default=0.07,
                    help="Resolución del vóxel (menor = más detalle, más lento)")
args = parser.parse_args()

import trimesh

print("Cargando malla PLY...")
mesh_ply = trimesh.load(args.ply, force="mesh")

print("Cargando nube de puntos NPY...")
nube = np.load(args.npy)

print("Cargando STL...")
mesh_stl = trimesh.load(args.stl, force="mesh")

print("Voxelizando malla PLY...")
mesh_ply.apply_translation(-mesh_ply.centroid)
mesh_ply.apply_scale(1.0 / mesh_ply.scale)
vox = mesh_ply.voxelized(pitch=args.voxel_pitch)
voxel_data = vox.matrix   # bool array

print("Generando figura...")
fig = plt.figure(figsize=(20, 6), facecolor="white")
fig.suptitle(
    "El mismo objeto en las cuatro representaciones empleadas en el pipeline",
    fontsize=16, fontweight="bold", y=1.02
)

gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.1)

ELEV, AZIM = 25, -55
DATOS = [
    ("Malla (.ply)",          "#2a6fba", "malla"),
    ("Nube de puntos (.npy)", "#c0392b", "nube"),
    ("Vóxel (binvox)",        "#27ae60", "voxel"),
    ("STL (.stl)",            "#d35400", "stl"),
]

axes = [fig.add_subplot(gs[i], projection="3d") for i in range(4)]

# Panel 1 — malla PLY
ax = axes[0]
v, f = mesh_ply.vertices, mesh_ply.faces
poly = Poly3DCollection(v[f], alpha=0.30, facecolor=DATOS[0][1], edgecolor="none")
ax.add_collection3d(poly)
ax.auto_scale_xyz(v[:, 0], v[:, 1], v[:, 2])

# Panel 2 — nube de puntos
ax = axes[1]
pts = nube if len(nube) <= 2048 else nube[np.random.choice(len(nube), 2048, replace=False)]
ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=2, c=DATOS[1][1], alpha=0.8, depthshade=True)

# Panel 3 — vóxel
ax = axes[2]
ax.voxels(voxel_data, facecolors=DATOS[2][1], edgecolors="none", alpha=0.65)

# Panel 4 — STL
ax = axes[3]
mesh_stl.apply_translation(-mesh_stl.centroid)
mesh_stl.apply_scale(1.0 / mesh_stl.scale)
vs, fs = mesh_stl.vertices, mesh_stl.faces
poly_s = Poly3DCollection(vs[fs], alpha=0.85, facecolor=DATOS[3][1], edgecolor="none")
ax.add_collection3d(poly_s)
ax.auto_scale_xyz(vs[:, 0], vs[:, 1], vs[:, 2])

# Estilo común
for ax, (title, color, _) in zip(axes, DATOS):
    ax.set_title(title, fontsize=14, fontweight="bold", color=color, pad=10)
    ax.tick_params(labelsize=7)
    ax.view_init(elev=ELEV, azim=AZIM)
    ax.set_facecolor("#f5f5f5")
    ax.grid(True, linewidth=0.3, alpha=0.4)
    ax.set_xlabel("X", fontsize=8, labelpad=1)
    ax.set_ylabel("Y", fontsize=8, labelpad=1)
    ax.set_zlabel("Z", fontsize=8, labelpad=1)

plt.tight_layout()
plt.savefig(args.out, dpi=200, bbox_inches="tight", facecolor="white")
print(f"\nGuardado: {args.out}")
