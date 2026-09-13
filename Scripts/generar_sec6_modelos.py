# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

OUT = "sec6_modelos_reducido.docx"
doc = Document()
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Cm(2.5)
    sec.top_margin  = sec.bottom_margin = Cm(2.5)

# ── Helpers ───────────────────────────────────────────────────────────────────

def h2(doc, t):
    p = doc.add_heading(t, level=2)
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(4)

def h3(doc, t):
    p = doc.add_heading(t, level=3)
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(3)

def h4(doc, t):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(2)
    r = p.add_run(t); r.bold = True; r.font.size = Pt(11)

def p(doc, t):
    par = doc.add_paragraph(t)
    par.paragraph_format.space_before = Pt(0); par.paragraph_format.space_after = Pt(5)
    for r in par.runs: r.font.size = Pt(11)
    return par

def nota(doc, t):
    par = doc.add_paragraph(t)
    par.paragraph_format.space_before = Pt(0); par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.left_indent = Cm(0.5)
    for r in par.runs:
        r.font.size = Pt(10); r.italic = True
        r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

def tabla_experimentos(doc, headers, filas):
    t = doc.add_table(rows=1 + len(filas), cols=len(headers))
    t.style = "Table Grid"
    t.paragraph_format if hasattr(t, "paragraph_format") else None
    # cabecera
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        for r in c.paragraphs[0].runs:
            r.bold = True; r.font.size = Pt(10)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    # filas
    for fi, fila in enumerate(filas):
        for ci, val in enumerate(fila):
            c = t.rows[fi + 1].cells[ci]
            c.text = str(val)
            for r in c.paragraphs[0].runs:
                r.font.size = Pt(10)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    # espacio post-tabla
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

# ── Instrucción ───────────────────────────────────────────────────────────────
nota(doc, "→ Este bloque reemplaza las subsecciones de Datasets, PCN, TopNet y PoinTr "
         "en el capítulo 6.")

# =============================================================================
# 6.x  Datasets
# =============================================================================
h3(doc, "6.x  Datasets")
p(doc,
    "Los datasets empleados —ShapeNet, Objaverse y Fantastic Breaks— se describen en la "
    "sección 3.1. Tras el proceso de generación y limpieza de roturas, el dataset final "
    "para E3 contiene 60 pares de Fantastic Breaks, 855 de ShapeNet y 397 de Objaverse.")

# =============================================================================
# 6.x  Generación de roturas sintéticas
# =============================================================================
h3(doc, "6.x  Generación de roturas sintéticas")
p(doc,
    "Partiendo de una nube densa (20.000 puntos) sobre cada malla limpia, se simula la "
    "pérdida de una porción del objeto mediante un corte con plano de orientación y posición "
    "aleatorias: se proyectan los puntos sobre la normal del plano y se descarta el lado que "
    "supere un percentil de corte, ajustado para eliminar entre el 10 % y el 40 % de la "
    "superficie. También se probaron variantes de corte esférico e intersección de dos planos, "
    "para diversificar los patrones de rotura.")
p(doc,
    "Cada rotura se valida antes de aceptarse, descartando casos con nube colapsada, "
    "degenerada en un plano o dividida en grupos desconectados; si falla, se reintenta "
    "con otro plano aleatorio hasta un máximo de intentos.")

# =============================================================================
# 6.x  Preprocesamiento y data loader
# =============================================================================
h3(doc, "6.x  Preprocesamiento y data loader")
p(doc,
    "Todos los pares se llevan a un formato común: nubes de 2.048 puntos XYZ (float32), "
    "centradas en el origen y escaladas al percentil 99 de la distancia al centro "
    "(en vez de la distancia máxima absoluta, para evitar que un punto atípico distorsione "
    "la escala). Se guardan como ficheros .npy con el mismo esquema, de modo que el data "
    "loader trata igual pares reales y sintéticos.")
p(doc,
    "Fantastic Breaks requirió alineación previa con ICP entre fragmento y modelo completo, "
    "tal como se detalla en la sección 3.1.3.")

# =============================================================================
# 6.x  PCN
# =============================================================================
h3(doc, "6.x  Baseline: PCN — Point Completion Network")

h4(doc, "Arquitectura")
p(doc,
    "La arquitectura de PCN se describe en la sección 2.4. "
    "En este proyecto se configura para generar 2.048 puntos (en vez de los 16.384 "
    "originales), con una nube gruesa intermedia de 128 puntos. "
    "Se usó la implementación qinglew/PCN-PyTorch.")

h4(doc, "Experimentos y resultados")
p(doc,
    "El baseline se entrenó de forma incremental (v1 a v5), corrigiendo en cada iteración "
    "un problema detectado en la anterior:")

tabla_experimentos(doc,
    ["Versión", "Datos", "Cambios", "CD-L1", "F-Score"],
    [
        ["v1", "FB + sint.", "Primer entrenamiento, 100 épocas", "0,0766", "0,019"],
        ["v3", "FB + sint.", "400 épocas", "0,0665", "0,024"],
        ["v4", "FB + sint.", "Filtro de outliers, más peso a rama coarse", "0,0641", "0,024"],
        ["v5", "FB + sint.", "Corrección de desalineación de centroide", "0,0630", "0,026"],
    ]
)

p(doc,
    "(La v2 se descartó por un bug en el cálculo de la pérdida, detectado antes de "
    "completarse el entrenamiento.)")
p(doc,
    "El cambio más relevante fue el de v4 a v5: al activar CENTRAR_EN_ROTO=True, cada par "
    "se recentra por el centroide del fragmento antes de pasarlo a la red. Sin esta "
    "corrección, el desplazamiento de ≈ 0,4 unidades entre el centroide del fragmento y "
    "el origen del objeto completo hace que el modelo colapse a una placa plana "
    "(CD ≈ 0,18–0,23). Este principio se mantuvo en todos los experimentos posteriores.")
p(doc,
    "Aun así, v5 alcanza F-Score = 0,026, lejos de resultados aceptables. "
    "Una prueba de sobreajuste a un único ejemplo real confirmó que la limitación es "
    "más del decoder tipo folding que de los datos, motivando la exploración de TopNet "
    "y finalmente PoinTr.")

# =============================================================================
# 6.x  TopNet
# =============================================================================
h3(doc, "6.x  Exploración con TopNet")

h4(doc, "Arquitectura")
p(doc,
    "La arquitectura de TopNet se describe en la sección 2.4. "
    "Se implementó en PyTorch puro, sin extensiones CUDA, para aislar si el techo "
    "bajo de PCN se debía al decoder o al encoder: al compartir el mismo encoder que PCN, "
    "cualquier diferencia de resultado es atribuible únicamente al decoder.")

h4(doc, "Experimentos y resultados")
p(doc,
    "TopNet se entrenó con la misma mezcla de datos y el mismo fix de centroide que "
    "PCN v5, para que la comparación fuera controlada:")

tabla_experimentos(doc,
    ["Modelo", "CD-L1", "F-Score"],
    [
        ["PCN v5",  "0,0630", "0,026"],
        ["TopNet",  "0,060",  "0,033"],
    ]
)

p(doc,
    "La mejora confirma que el decoder tipo folding de PCN era un factor limitante, "
    "pero sigue siendo moderada (F-Score = 0,033). El cuello de botella principal es "
    "la compresión en un único vector global de 1.024 d, que impide razonar sobre "
    "geometría local. Esto motivó el salto a PoinTr, que sustituye también el encoder.")

# =============================================================================
# 6.x  PoinTr
# =============================================================================
h3(doc, "6.x  Modelo principal: PoinTr")

h4(doc, "Arquitectura")
p(doc,
    "La arquitectura de PoinTr se describe en la sección 2.4. "
    "Se usó la implementación oficial (yuxumin/PoinTr). "
    "Las extensiones CUDA (chamfer_dist, pointnet2_ops, knn_cuda) se sustituyeron "
    "por versiones en PyTorch puro para compatibilidad con Google Colab "
    "(coste: ×1,4 en velocidad).")

doc.save(OUT)
print(f"Guardado: {OUT}")
