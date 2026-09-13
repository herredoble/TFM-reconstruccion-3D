# -*- coding: utf-8 -*-
"""
Genera imágenes PNG de las fórmulas matemáticas para el Word.
Uso: python Scripts/generar_formulas.py
Requiere: matplotlib numpy
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("figuras_formulas")
OUT.mkdir(exist_ok=True)

DPI = 280

def guardar_formula(nombre, lineas, escala=1.6, sep=0.32):
    """
    lineas : lista de strings mathtext (una por línea de la fórmula).
    sep    : separación vertical entre líneas (en fracción del alto total).
    """
    n    = len(lineas)
    alto = max(1.2, n * sep * escala * 2.2)
    fig  = plt.figure(figsize=(10, alto), facecolor="white")
    ax   = fig.add_axes([0, 0, 1, 1])   # sin márgenes automáticos
    ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # Distribuir líneas con separación uniforme
    ys = [0.5 + (n - 1) / 2 * sep - i * sep for i in range(n)]
    # Reclamp si se salen
    if max(ys) > 0.95 or min(ys) < 0.05:
        span = max(ys) - min(ys) if n > 1 else 1
        ys = [0.5 + (y - sum(ys)/n) / (span + 1e-9) * 0.8 for y in ys]

    for y, linea in zip(ys, lineas):
        ax.text(0.5, y, linea,
                ha="center", va="center",
                fontsize=18 * escala,
                transform=ax.transAxes)

    ruta = OUT / f"{nombre}.png"
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight", facecolor="white",
                pad_inches=0.15)
    plt.close(fig)
    print(f"  Guardada: {ruta}")


# ── 1. IoU ────────────────────────────────────────────────────────────────────
guardar_formula("formula_iou", [
    r"$\mathrm{IoU} = \dfrac{|V_{pred} \cap V_{gt}|}{|V_{pred} \cup V_{gt}|}$"
])

# ── 2. Chamfer Distance ───────────────────────────────────────────────────────
# Una línea por término para evitar overlap de subíndices con denominadores
guardar_formula("formula_chamfer", [
    r"$\mathrm{CD}(P,\,Q) = \dfrac{1}{|P|}\,\sum_{p \in P}\,\min_{q \in Q}\,\|p-q\|_2"
    r"\;+\;\dfrac{1}{|Q|}\,\sum_{q \in Q}\,\min_{p \in P}\,\|q-p\|_2$",
], escala=1.1, sep=0.0)

# ── 3. F-Score ────────────────────────────────────────────────────────────────
# Separación mayor para que las fracciones no colisionen
guardar_formula("formula_fscore", [
    r"$\mathrm{Prec}(t) \;=\; \dfrac{\#\{p\in P\,:\,d(p,Q)<t\}}{|P|}$",
    r"$\mathrm{Rec}(t)  \;=\; \dfrac{\#\{q\in Q\,:\,d(q,P)<t\}}{|Q|}$",
    r"$F\!\mathrm{-Score}(t) \;=\; \dfrac{2\cdot\mathrm{Prec}(t)\cdot\mathrm{Rec}(t)}{\mathrm{Prec}(t)+\mathrm{Rec}(t)}$",
], escala=1.3, sep=0.38)

# ── 4. Sørensen-Dice ─────────────────────────────────────────────────────────
guardar_formula("formula_dice", [
    r"$\mathrm{DSC} = \dfrac{2\,|V_{pred} \cap V_{gt}|}{|V_{pred}| + |V_{gt}|}$"
])

# ── 5. Precisión vóxel ────────────────────────────────────────────────────────
guardar_formula("formula_precision_voxel", [
    r"$\mathrm{Prec}_{vox} = \dfrac{|V_{pred} \cap V_{gt}|}{|V_{pred}|}$"
])

# ── 6. Recall vóxel ───────────────────────────────────────────────────────────
guardar_formula("formula_recall_voxel", [
    r"$\mathrm{Rec}_{vox} = \dfrac{|V_{pred} \cap V_{gt}|}{|V_{gt}|}$"
])

print("\nListo. Archivos en:", OUT.resolve())
print("Insértalas en Word con: Insertar → Imágenes → selecciona el PNG.")
print("Recomendado: centrar la imagen y usar 'ajuste de texto: en línea con el texto'.")
