# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

IMG = Path("figuras_formulas")
OUT = "formulas_metricas_v3.docx"

doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin  = sec.bottom_margin = Cm(2.5)

def titulo(doc, texto):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(1)
    r = p.add_run(texto)
    r.bold = True; r.font.size = Pt(11)
    return p

def linea(doc, texto):
    p = doc.add_paragraph(texto)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(2)
    for r in p.runs: r.font.size = Pt(10.5)
    return p

def img(doc, ruta, ancho_cm=10):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    p.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
    return p

# ── Cabecera ──────────────────────────────────────────────────────────────────
h = doc.add_heading("2.3  Métricas de evaluación", level=2)
h.paragraph_format.space_after = Pt(4)

# ── 1. IoU ────────────────────────────────────────────────────────────────────
titulo(doc, "Intersección sobre Unión (IoU)")
linea(doc,
    "Solapamiento entre el volumen de vóxeles predicho y el real. "
    "Varía entre 0 (ninguna coincidencia) y 1 (predicción perfecta). "
    "Métrica principal en E2 (Pix2Vox++).")
img(doc, IMG / "formula_iou.png", ancho_cm=7)

# ── 2. Chamfer Distance ───────────────────────────────────────────────────────
titulo(doc, "Distancia de Chamfer (CD-L1)")
linea(doc,
    "Media de las distancias mínimas entre dos nubes de puntos en ambas direcciones. "
    "Un valor menor indica superficies más parecidas. "
    "Métrica principal en E3 (shape completion).")
img(doc, IMG / "formula_chamfer.png", ancho_cm=13)

# ── 3. F-Score ────────────────────────────────────────────────────────────────
titulo(doc, "F-Score a umbral t")
linea(doc,
    "Media armónica de la precisión y el recall sobre nubes de puntos para un umbral "
    "de distancia t. Más interpretable que CD y menos sensible a valores atípicos. "
    "Se reporta a t = 0,01 / 0,02 / 0,05 (1–5 % de la escala del objeto).")
img(doc, IMG / "formula_fscore.png", ancho_cm=9)

# ── 4. Sørensen-Dice ─────────────────────────────────────────────────────────
titulo(doc, "Coeficiente de Sørensen-Dice (DSC)")
linea(doc,
    "Compara el doble de la intersección con la suma de los vóxeles ocupados en el "
    "volumen predicho y en el real. Varía entre 0 y 1; complementa al IoU siendo "
    "más sensible en zonas de alto solapamiento.")
img(doc, IMG / "formula_dice.png", ancho_cm=8)

# ── 5. Precisión vóxel ────────────────────────────────────────────────────────
titulo(doc, "Precisión vóxel (Prec_vox)")
linea(doc,
    "Proporción de vóxeles predichos como ocupados que pertenecen realmente al objeto. "
    "Un valor bajo indica que el modelo genera volumen de más (falsos positivos).")
img(doc, IMG / "formula_precision_voxel.png", ancho_cm=7)

# ── 6. Recall vóxel ───────────────────────────────────────────────────────────
titulo(doc, "Recall vóxel (Rec_vox)")
linea(doc,
    "Proporción del objeto real que ha sido reconstruida. "
    "Un valor bajo indica que el modelo omite partes de la geometría (falsos negativos).")
img(doc, IMG / "formula_recall_voxel.png", ancho_cm=7)

doc.save(OUT)
print(f"Guardado: {OUT}")
