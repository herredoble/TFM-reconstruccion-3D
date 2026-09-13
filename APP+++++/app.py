"""
app.py — Etapa 5: app end-to-end.

    [5 fotos de la taza rota] -> E2 -> [nube rota] -> E3 -> [nube reparada]
        -> E4 -> [STL watertight + report.json]

Pensada para correr dentro de un notebook de Colab (ver
colab_run_app.ipynb) que ya tiene Drive montado y el checkpoint/módulo de
Pix2Vox++ accesibles. Ver avisos en pipeline_e2.py sobre:
  - modelo_pix2vox.py todavía vive en Drive, no en el repo (pendiente
    de mover — asumido tal cual para esta primera versión de la app).
  - Los 5 ángulos de cámara son fijos: por eso esta app NO deja subir 5
    fotos libres, sino que guía al usuario paso a paso, una foto por
    ángulo, con una referencia visual de cómo colocar la cámara.
"""

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

import gradio as gr

from pipeline_e2 import fotos_a_nube, DEFAULT_CHECKPOINT_NAME as DEFAULT_CKPT_E2
from pipeline_e3 import reparar_nube, DEFAULT_CHECKPOINT_VERSION as DEFAULT_CKPT_E3
from pipeline_e4 import nube_a_stl, Config as ConfigE4


# ─────────────────────────────────────────────────────────────────────────
# GUÍA DE LAS 5 FOTOS
# ─────────────────────────────────────────────────────────────────────────
# Mismos ángulos que en Fantastik_Break_preparacion_Pix2Vox_E2_E3.ipynb
# (Celda 5, VISTAS_5). azimuth 0° = de frente al asa/marca que el usuario
# elija como "frente"; elevación = cuánto se levanta la cámara sobre el
# horizonte del objeto.

VISTAS = [
    {
        "id": "vista_00",
        "titulo": "Foto 1 — Frontal",
        "instruccion": (
            "Coloca la taza rota sobre una superficie lisa y con buena luz. "
            "Ponte justo enfrente, a la altura del objeto, y baja un poco la "
            "cámara (~20° por debajo de la horizontal, mirando ligeramente "
            "hacia abajo)."
        ),
    },
    {
        "id": "vista_05",
        "titulo": "Foto 2 — Trasera-izquierda",
        "instruccion": (
            "Rodea el objeto hasta quedar detrás y a tu izquierda respecto a "
            "la Foto 1 (gira unos 225° alrededor de la taza). Misma altura de "
            "cámara que en la Foto 1."
        ),
    },
    {
        "id": "vista_10",
        "titulo": "Foto 3 — Lateral derecho, más alto",
        "instruccion": (
            "Vuelve a un lateral (90° respecto a la Foto 1, el lado "
            "contrario a la Foto 2) y esta vez eleva más la cámara, mirando "
            "más hacia abajo (~40°)."
        ),
    },
    {
        "id": "vista_14",
        "titulo": "Foto 4 — Lateral izquierdo, más alto",
        "instruccion": (
            "El lateral opuesto a la Foto 3 (270° respecto a la Foto 1), "
            "manteniendo la misma elevación alta (~40°)."
        ),
    },
    {
        "id": "vista_19",
        "titulo": "Foto 5 — Cenital",
        "instruccion": (
            "Desde el mismo lateral que la Foto 4, eleva aún más la cámara "
            "para mirar casi desde arriba (~60°), abarcando bien la zona de "
            "la rotura desde el interior si es visible."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────
# LÓGICA DE LA APP
# ─────────────────────────────────────────────────────────────────────────

def reconstruir(
    foto_00, foto_05, foto_10, foto_14, foto_19,
    checkpoint_e2, checkpoint_e3,
    progreso=gr.Progress(),
):
    fotos = [foto_00, foto_05, foto_10, foto_14, foto_19]
    if any(f is None for f in fotos):
        raise gr.Error("Faltan fotos — sube las 5 antes de reconstruir (una por cada ángulo).")

    try:
        progreso(0.05, desc="Etapa 2 — Pix2Vox++: fotos → nube de puntos rota...")
        nube_rota = fotos_a_nube(fotos, checkpoint_name=checkpoint_e2)

        progreso(0.40, desc="Etapa 3 — PoinTr: reparando la nube de puntos...")
        nube_completa = reparar_nube(nube_rota, checkpoint_version=checkpoint_e3)

        progreso(0.70, desc="Etapa 4 — Poisson + limpieza: generando malla STL...")
        salida_dir = Path(tempfile.mkdtemp(prefix="tfm_e5_"))
        ruta_stl = salida_dir / "taza_reparada.stl"
        report = nube_a_stl(nube_completa, ruta_stl, config=ConfigE4())

        progreso(1.0, desc="Listo.")

        if report["volumen_mm3"]:
            texto_volumen = f"{report['volumen_mm3']:.1f} mm³"
        else:
            texto_volumen = "N/D (malla no watertight)"

        estado = (
            f"✅ Reconstrucción completada.\n\n"
            f"- Checkpoint E2 (Pix2Vox++): {checkpoint_e2}\n"
            f"- Checkpoint E3 (PoinTr): {checkpoint_e3}\n"
            f"- Watertight: {report['watertight']}\n"
            f"- Errores de malla reparados: {report['errores_reparados']}\n"
            f"- Volumen estimado: {texto_volumen}"
        )

        return str(ruta_stl), str(ruta_stl), estado

    except Exception as exc:  # noqa: BLE001 — queremos mostrar el error al usuario en la UI
        traceback.print_exc()
        raise gr.Error(f"Fallo en el pipeline: {exc}")


# ─────────────────────────────────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────────────────────────────────

def construir_app() -> gr.Blocks:
    with gr.Blocks(title="TFM — Reconstrucción 3D de tazas rotas") as demo:
        gr.Markdown(
            "# 🏺 De taza rota a STL imprimible\n"
            "Sube 5 fotos siguiendo la guía de ángulos de abajo (importante: "
            "el modelo se entrenó con estos ángulos concretos, fotos libres "
            "dan peores resultados). El pipeline reconstruye la geometría "
            "que falta y te devuelve un STL listo para imprimir."
        )

        with gr.Row():
            inputs_fotos = []
            for vista in VISTAS:
                with gr.Column():
                    gr.Markdown(f"**{vista['titulo']}**\n\n{vista['instruccion']}")
                    img = gr.Image(label=vista["titulo"], type="filepath")
                    inputs_fotos.append(img)

        with gr.Accordion("Opciones avanzadas (checkpoints)", open=False):
            checkpoint_e2 = gr.Textbox(
                label="Checkpoint Pix2Vox++ (E2)", value=DEFAULT_CKPT_E2
            )
            checkpoint_e3 = gr.Textbox(
                label="Checkpoint PoinTr (E3)", value=DEFAULT_CKPT_E3
            )

        boton = gr.Button("🔧 Reconstruir taza", variant="primary")

        estado_texto = gr.Textbox(label="Estado", interactive=False)
        with gr.Row():
            visor_stl = gr.Model3D(label="Previsualización 3D")
            descarga_stl = gr.File(label="Descargar STL")

        boton.click(
            fn=reconstruir,
            inputs=[*inputs_fotos, checkpoint_e2, checkpoint_e3],
            outputs=[visor_stl, descarga_stl, estado_texto],
        )

    return demo


if __name__ == "__main__":
    app = construir_app()
    # share=True para poder acceder desde fuera de Colab (útil para demo).
    app.launch(share=True)
