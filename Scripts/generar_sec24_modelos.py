# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Cm, Pt

OUT = "seccion_24_modelos_v2.docx"
doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin  = sec.bottom_margin = Cm(2.5)

def h2(doc, t):
    p = doc.add_heading(t, level=2)
    p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(4)

def h3(doc, t):
    p = doc.add_heading(t, level=3)
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(2)

def linea(doc, t):
    p = doc.add_paragraph(t)
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(4)
    for r in p.runs: r.font.size = Pt(10.5)
    return p

# ── 2.4 ───────────────────────────────────────────────────────────────────────
h2(doc, "2.4  Modelos de aprendizaje profundo empleados en el pipeline")

linea(doc,
    "El pipeline integra cinco modelos preentrenados, cada uno responsable de una "
    "etapa diferente. Se describen a continuación junto con la etapa donde se usan.")

# ── SAM ───────────────────────────────────────────────────────────────────────
h3(doc, "SAM — Segment Anything Model  (E1)")
linea(doc,
    "Vision Transformer (ViT-H) entrenado sobre más de 1.000 M de máscaras "
    "(Meta AI, Kirillov et al. 2023). Se usa en E1 para eliminar el fondo de "
    "las fotografías del objeto roto: a partir de un punto o caja sobre el objeto, "
    "genera la máscara de segmentación que aísla el objeto del entorno.")

# ── Pix2Vox++ ─────────────────────────────────────────────────────────────────
h3(doc, "Pix2Vox++ — Reconstrucción 3D multi-vista  (E2)")
linea(doc,
    "CNN encoder-decoder con módulos Merger y Refiner (Xie et al. 2020). "
    "Toma N imágenes 2D del objeto desde distintos puntos de vista y predice "
    "una cuadrícula de vóxeles 32³. El Merger decide qué partes de cada vista "
    "son más fiables y las fusiona; el Refiner corrige el volumen resultante. "
    "Se parte del modelo preentrenado en ShapeNet con fine-tuning sobre vasijas.")

# ── PCN ───────────────────────────────────────────────────────────────────────
h3(doc, "PCN — Point Completion Network  (E3, baseline)")
linea(doc,
    "Encoder PointNet (MLPs + max-pooling → vector global 1.024 d) + decoder "
    "FoldingNet en dos etapas: nube gruesa de 128 puntos → expansión a 2.048 "
    "mediante folding sobre rejilla 2D (Yuan et al. 2018, ≈ 4 M parámetros). "
    "Se entrenó como referencia antes de explorar arquitecturas más complejas.")

# ── TopNet ────────────────────────────────────────────────────────────────────
h3(doc, "TopNet — Decoder jerárquico en árbol  (E3, exploración)")
linea(doc,
    "Mismo encoder que PCN, pero con decoder en árbol jerárquico de MLPs: "
    "cada nodo se ramifica en nodos hijo nivel a nivel con skip connections "
    "al vector global (Tchapmi et al. 2019, ≈ 4 M parámetros). "
    "Su resultado permitió confirmar que el cuello de botella era el vector global, "
    "no el tipo de decoder, motivando el salto a PoinTr.")

# ── PoinTr ────────────────────────────────────────────────────────────────────
h3(doc, "PoinTr — Point Transformer  (E3, modelo principal)")
linea(doc,
    "Trata la completación como una tarea sequence-to-sequence entre grupos de puntos "
    "(Yu et al. 2021, 42,2 M parámetros). La nube parcial se tokeniza con DGCNN; "
    "un transformer encoder-decoder combina esos tokens con proxy points "
    "(posiciones estimadas de la región faltante); y una cabeza coarse + FoldingNet "
    "local genera la nube completa. "
    "El modelo final (v6_obj_sn, 500 épocas, 2.501 pares ShapeNet + Objaverse) "
    "obtiene CD-L1 = 0,0245 y F-Score = 0,45 sobre el conjunto de test.")

doc.save(OUT)
print(f"Guardado: {OUT}")
