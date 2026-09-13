# -*- coding: utf-8 -*-
"""
Genera figura_experimentos_e3.png:
  Comparativa de todos los experimentos E3 (PCN, TopNet, PoinTr)
  con CD-L1 (barras, eje izq.) y F-Score (línea, eje dcha.)

Uso: python Scripts/generar_figura_experimentos.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Datos de todos los experimentos ───────────────────────────────────────────
# Orden cronológico. F-Score=None donde no se midió o no es comparable.
EXPERIMENTOS = [
    # etiqueta,           modelo,   n_pares, cd_l1,  f_score
    ("PCN v1",           "PCN",      400,    0.0770,  None),
    ("PCN v3",           "PCN",      400,    0.0665,  0.0240),
    ("PCN v4",           "PCN",      400,    0.0641,  0.0236),
    ("PCN v5",           "PCN",      400,    0.0630,  0.0257),
    ("TopNet",           "TopNet",   400,    0.0600,  0.0329),
    ("PoinTr v4\n(61p)", "PoinTr",    61,    0.0569,  0.0285),
    ("PoinTr v5\n(397p)","PoinTr",   397,    0.0306,  None),
    ("PoinTr v6\n(2501p)","PoinTr", 2501,    0.0245,  0.4547),
    ("PoinTr v6\n+FB",   "PoinTr",  2561,    0.0297,  None),
]

COLORES = {"PCN": "#1565C0", "TopNet": "#E65100", "PoinTr": "#1B5E20"}

etiquetas = [e[0] for e in EXPERIMENTOS]
modelos   = [e[1] for e in EXPERIMENTOS]
cd        = [e[3] for e in EXPERIMENTOS]
fs_raw    = [e[4] for e in EXPERIMENTOS]

x = np.arange(len(etiquetas))

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(13, 5.5), facecolor="white")
ax2 = ax1.twinx()

# Barras CD-L1
bar_colors = [COLORES[m] for m in modelos]
bars = ax1.bar(x, cd, color=bar_colors, alpha=0.82, width=0.55, zorder=2)

# Valor encima de cada barra
for xi, val in zip(x, cd):
    ax1.text(xi, val + 0.0008, f"{val:.4f}", ha="center", va="bottom",
             fontsize=8, color="#222222")

# Línea F-Score (solo donde está disponible)
fs_x   = [xi for xi, v in zip(x, fs_raw) if v is not None]
fs_val = [v  for v       in fs_raw        if v is not None]
ax2.plot(fs_x, fs_val, "D--", color="#880E4F", linewidth=1.6,
         markersize=6, zorder=3, label="F-Score")
for xi, v in zip(fs_x, fs_val):
    ax2.text(xi + 0.08, v + 0.005, f"{v:.3f}", fontsize=8,
             color="#880E4F", va="bottom")

# ── Anotaciones de hitos ──────────────────────────────────────────────────────
# Corrección de centroide (PCN v5)
ax1.annotate("Fix centroide", xy=(3, 0.0630), xytext=(3, 0.078),
             fontsize=8, color="#1565C0", ha="center",
             arrowprops=dict(arrowstyle="->", color="#1565C0", lw=1.1))

# Salto de datos PoinTr v5→v6
ax1.annotate("×10 datos", xy=(7, 0.0245), xytext=(7.5, 0.045),
             fontsize=8, color="#1B5E20", ha="center",
             arrowprops=dict(arrowstyle="->", color="#1B5E20", lw=1.1))

# FB perjudica
ax1.annotate("+FB real\n(+21% CD)", xy=(8, 0.0297), xytext=(8, 0.055),
             fontsize=8, color="#B71C1C", ha="center",
             arrowprops=dict(arrowstyle="->", color="#B71C1C", lw=1.1))

# Separador visual entre modelos
for sep_x in [3.5, 4.5]:
    ax1.axvline(sep_x, color="#cccccc", linewidth=0.8, linestyle="--", zorder=1)

# ── Ejes y leyenda ────────────────────────────────────────────────────────────
ax1.set_xticks(x)
ax1.set_xticklabels(etiquetas, fontsize=9)
ax1.set_ylabel("CD-L1  (↓ mejor)", fontsize=10)
ax1.set_ylim(0, 0.095)
ax1.set_xlabel("")
ax1.grid(axis="y", alpha=0.3, zorder=0)

ax2.set_ylabel("F-Score  (↑ mejor)", fontsize=10, color="#880E4F")
ax2.tick_params(axis="y", colors="#880E4F")
ax2.set_ylim(0, 0.60)

leyenda = [
    mpatches.Patch(color=COLORES["PCN"],    label="PCN"),
    mpatches.Patch(color=COLORES["TopNet"], label="TopNet"),
    mpatches.Patch(color=COLORES["PoinTr"], label="PoinTr"),
    plt.Line2D([0], [0], color="#880E4F", marker="D", linestyle="--",
               markersize=5, label="F-Score"),
]
ax1.legend(handles=leyenda, loc="upper right", fontsize=9,
           framealpha=0.9, ncol=2)

ax1.set_title(
    "Evolución de resultados E3 — PCN · TopNet · PoinTr\n"
    "CD-L1 (barras, eje izq.) y F-Score (línea, eje dcha.)",
    fontsize=11, fontweight="bold", pad=10
)

plt.tight_layout()
fig.savefig("figura_experimentos_e3.png", dpi=220, bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("Guardado: figura_experimentos_e3.png")
