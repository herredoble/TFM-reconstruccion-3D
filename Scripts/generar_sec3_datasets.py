# -*- coding: utf-8 -*-
"""
Genera sec3_datasets_adicionales.docx con el texto para añadir a la sección 3.1
(Objaverse y Fantastic Breaks), listo para copiar en el TFM.
"""
from docx import Document
from docx.shared import Cm, Pt

OUT = "sec3_datasets_adicionales.docx"
doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin  = sec.bottom_margin = Cm(2.5)

def h3(doc, t):
    p = doc.add_heading(t, level=3)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(3)

def p(doc, t):
    par = doc.add_paragraph(t)
    par.paragraph_format.space_before = Pt(0)
    par.paragraph_format.space_after  = Pt(5)
    for r in par.runs: r.font.size = Pt(11)
    return par

def nota_insercion(doc, t):
    par = doc.add_paragraph(t)
    par.paragraph_format.space_before = Pt(8)
    par.paragraph_format.space_after  = Pt(2)
    for r in par.runs:
        r.font.size = Pt(10)
        r.italic = True
    return par

# ── Instrucción de inserción ──────────────────────────────────────────────────
nota_insercion(doc,
    "→ INSERTAR: sustituir el último párrafo de 3.1 (el que empieza por "
    "\"Además de estas 2.170 mallas…\") por el bloque siguiente.")

# ── Párrafo puente (reemplaza al párrafo actual) ──────────────────────────────
p(doc,
    "Además de estas 2.170 mallas, el proyecto emplea otros dos repositorios "
    "en la fase de shape completion (capítulo 6), descritos a continuación.")

# ── 3.1.2 Objaverse ───────────────────────────────────────────────────────────
h3(doc, "3.1.2  Objaverse")
p(doc,
    "Objaverse (Deitke et al., 2023) es un repositorio de código abierto con más de "
    "800.000 modelos 3D anotados, de calidad y estilo muy heterogéneos. "
    "A diferencia de ShapeNet, no está organizado en categorías rígidas: "
    "los objetos provienen de artistas y estudios de diseño, lo que aporta "
    "mayor variedad geométrica y visual.")
p(doc,
    "De este repositorio se seleccionaron y limpiaron 131 mallas de la supercategoría "
    "de vasijas (tazas, jarras, cuencos), aplicando los mismos criterios de filtrado "
    "que para ShapeNet (mínimo 1.000 caras, centrado, escala unitaria). "
    "Estos modelos se emplean exclusivamente como objetos completos para generar "
    "roturas sintéticas adicionales en E3; no existen pares de rotura reales en Objaverse.")

# ── 3.1.3 Fantastic Breaks ────────────────────────────────────────────────────
h3(doc, "3.1.3  Fantastic Breaks")
p(doc,
    "Fantastic Breaks (Lamb et al., 2023) es el único de los tres datasets que ofrece "
    "pares reales (fragmento roto, objeto completo) en lugar de roturas sintéticas. "
    "Contiene 150 objetos domésticos físicamente rotos, escaneados en 3D junto con "
    "sus contrapartes completas mediante un escáner de luz estructurada. "
    "Las nubes de puntos resultantes presentan ruido de escáner, densidad irregular "
    "y pequeñas inconsistencias de alineación entre el fragmento y el objeto completo.")
p(doc,
    "De este conjunto se filtraron los pares de la supercategoría de vasijas "
    "(mug, bowl, jar, cup), obteniendo 61 pares utilizables. "
    "La alineación previa de cada par se realizó aplicando la transformación incluida "
    "en los metadatos del dataset y refinándola con ICP (Iterative Closest Point), "
    "ya que fragmento y objeto completo provienen de escaneos independientes. "
    "Dado su tamaño reducido (61 pares frente a los 2.501 sintéticos del conjunto final), "
    "se usa principalmente como conjunto de evaluación en condiciones reales "
    "y, de forma experimental, como datos de entrenamiento adicional.")

doc.save(OUT)
print(f"Guardado: {OUT}")
print("Pégalo en el TFM tras el último párrafo de la sección 3.1.")
