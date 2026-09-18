# -*- coding: utf-8 -*-
"""
Genera figura_gantt_anexo.png — Diagrama de Gantt para el anexo del TFM.
Uso: python Scripts/generar_gantt_anexo.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from datetime import datetime

START = datetime(2026, 7, 1)
END   = datetime(2026, 9, 15)
TOTAL = (END - START).days   # 76 días

def d(s):
    return (datetime.strptime(s, "%Y-%m-%d") - START).days

GRUPOS = [
    {
        "lane": "Reconstrucción 3D",
        "band": "#E3F2FD",
        "tareas": [
            ("Preprocesado\nde datos",      "2026-07-01", "2026-07-15", "#42A5F5"),
            ("Fine-tuning\nPix2Vox",        "2026-07-15", "2026-08-15", "#1E88E5"),
            ("Fine-tuning\ntazas rotas",    "2026-08-01", "2026-09-01", "#1565C0"),
        ]
    },
    {
        "lane": "Reparación IA",
        "band": "#E8F5E9",
        "tareas": [
            ("Preprocesado\nde datos",      "2026-07-01", "2026-07-15", "#43A047"),
            ("Reparación\nbaselines PCN",   "2026-07-15", "2026-08-15", "#388E3C"),
            ("Reparación\nPoinTr v1→v6","2026-08-01", "2026-08-27", "#1B5E20"),
        ]
    },
    {
        "lane": "Integración\ny entrega",
        "band": "#FFF8E1",
        "tareas": [
            ("Contratos\ninterfaz",         "2026-07-06", "2026-07-11", "#7B1FA2"),
            ("Generación\nde STL",          "2026-08-15", "2026-09-06", "#E65100"),
            ("App demo\nREBUILD3D",         "2026-09-01", "2026-09-12", "#C62828"),
            ("Memoria y\ndocumentación",    "2026-08-15", "2026-09-13", "#4E342E"),
            ("Repositorio\nGitHub",         "2026-09-12", "2026-09-14", "#37474F"),
        ]
    }
]

MILESTONES = [
    ("PoinTr BEST\nCD=0.0245", "2026-08-27", "#1B5E20",  0),
    ("App\nfuncional",          "2026-09-12", "#C62828", -4),
    ("Entrega",                 "2026-09-15", "#B71C1C", +3),
]

tareas_flat = []
separadores = []
for grupo in GRUPOS:
    separadores.append(len(tareas_flat))
    for t in grupo["tareas"]:
        tareas_flat.append((t, grupo["band"], grupo["lane"]))

n = len(tareas_flat)

LEFT_MARGIN  = -14   # julio pegado al borde izquierdo
RIGHT_EXTRA  = 5
BAR_HEIGHT   = 0.78
MIN_BAR_INSIDE = 4   # días mínimos para texto dentro

fig, ax = plt.subplots(figsize=(17, 9.5), facecolor="white")

# Swim-lane backgrounds y etiquetas
sep_indices = separadores + [n]
for g, grupo in enumerate(GRUPOS):
    y0 = n - sep_indices[g+1] - 0.5
    y1 = n - sep_indices[g]   + 0.5
    ax.axhspan(y0, y1, color=grupo["band"], zorder=0, alpha=0.7)
    ymid = (y0 + y1) / 2
    ax.text(LEFT_MARGIN / 2, ymid, grupo["lane"],
            ha="center", va="center",
            fontsize=10, color="#1a1a1a", fontweight="bold", linespacing=1.5)

# Barras
for i, ((nombre, ini, fin, color), band, lane) in enumerate(tareas_flat):
    x0, x1 = d(ini), d(fin)
    dur = x1 - x0
    yi = n - 1 - i

    ax.barh(yi, dur, left=x0, height=BAR_HEIGHT,
            color=color, alpha=0.92, zorder=2,
            edgecolor="white", linewidth=0.8)

    if dur >= MIN_BAR_INSIDE:
        txt = ax.text(x0 + dur / 2, yi, nombre,
                      ha="center", va="center",
                      fontsize=10.5, color="white", fontweight="bold",
                      linespacing=1.25, zorder=3)
        txt.set_path_effects([pe.withStroke(linewidth=2.8, foreground=color)])
    else:
        # Barra muy corta (Repositorio 2 días): texto encima
        ax.text(x0 + dur / 2, yi + BAR_HEIGHT / 2 + 0.05, nombre.replace("\n", " "),
                ha="center", va="bottom",
                fontsize=9, color=color, fontweight="bold", zorder=3)

# Milestones
for label, fecha, color, offset in MILESTONES:
    xm = d(fecha)
    ax.plot(xm, -0.9, "v", color=color, markersize=13, zorder=5, clip_on=False)
    ax.text(xm + offset, -1.6, label, ha="center", va="top",
            fontsize=9.5, color=color, fontweight="bold", linespacing=1.3)

# Separadores entre grupos
for si in separadores[1:]:
    ax.axhline(n - si - 0.5, color="#888888", lw=1.0, linestyle="--", zorder=1)

# Rejilla temporal
for ms in ["2026-07-01", "2026-08-01", "2026-09-01"]:
    ax.axvline(d(ms), color="#aaaaaa", lw=1.0, zorder=1)
for w in range(0, TOTAL + 1, 7):
    ax.axvline(w, color="#eeeeee", lw=0.5, zorder=0)

# Línea separadora etiquetas / diagrama
ax.axvline(0, color="#555555", lw=1.3, zorder=3)

# Ejes
ticks  = [d("2026-07-01"), d("2026-08-01"), d("2026-09-01"), TOTAL]
labels = ["Jul 2026", "Ago 2026", "Sep 2026", "15 Sep"]
ax.set_xticks(ticks)
ax.set_xticklabels(labels, fontsize=12)
ax.set_xlim(LEFT_MARGIN, TOTAL + RIGHT_EXTRA)
ax.set_ylim(-3.2, n - 0.15)
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)

plt.tight_layout()
fig.savefig("Latex/imagenes/figura_gantt_anexo.png",
            dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Guardado: Latex/imagenes/figura_gantt_anexo.png")
