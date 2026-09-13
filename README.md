# TFM — Reconstrucción y reparación 3D de objetos rotos

De fotos de un objeto roto → nube de puntos reconstruida → malla reparada → archivo STL imprimible.

**Equipo:** Raquel Roca · Rocío · Álvaro · Almu · Luis  
**Entrega:** 15 septiembre 2026  
**Última actualización:** 13 septiembre 2026

---

## Pipeline completo

```
[Fotos JPG]
    ↓ E2+++++  Pix2Vox++ (reconstrucción voxel 32³ → nube 2048 pts)
[Nube de puntos rota · numpy (2048,3)]
    ↓ E3+++++  PoinTr / PCN (shape completion)
[Nube completa · numpy (2048,3)]
    ↓ E4+++++  Poisson reconstruction + watertight
[Malla reparada · .STL]
    ↓ APP+++++ Gradio app (REBUILD3D)
[Demo interactiva end-to-end]
```

**Mejor resultado E3:** PoinTr v6_obj_sn · CD = 0.0245 · F-Score = 0.4547  
**Demo funcional:** app Gradio con fotos reales de tazas rotas → STL

---

## Estructura del repositorio

```
TFM-reconstruccion-3D/
│
├── APP+++++/                        ← App Gradio (scripts Python)
│   ├── app.py                       — interfaz Gradio REBUILD3D
│   ├── pipeline_e2.py               — módulo reconstrucción Pix2Vox++
│   ├── pipeline_e3.py               — módulo reparación PoinTr
│   ├── pipeline_e4.py               — módulo STL watertight
│   └── colab_run_app.ipynb          — lanzar la app desde Colab
│
├── E2+++++/                         ← Reconstrucción 3D (Pix2Vox++)
│   ├── [FINAL] [ACM][NO TOCAR] Fine tuning PIx2Vox Rotas.ipynb
│   ├── [FINAL] [ACM] Evaluacion_Tazas_Rotas.ipynb
│   ├── [FINAL] Fantastik_Break_preparacion_Pix2Vox_E2_E3.ipynb
│   ├── [FINAL] Pix2vox++_Ampliado.ipynb
│   ├── modelo_pix2vox.py            — arquitectura Pix2Vox++
│   └── checkpoints/                 — pesos entrenados (.pth — en Drive)
│
├── E3+++++/                         ← Reparación de nubes de puntos
│   ├── notebooks/                   — entrenamiento PCN y PoinTr (v1→v6)
│   │   ├── colab_entrenar_pcn_v4/v5.ipynb      (PCN · CD=0.0641/0.0630)
│   │   ├── colab_entrenar_pointr_v6_all.ipynb  (PoinTr · CD=0.0245 ← mejor)
│   │   ├── dataset.py / train.py / evaluate.py
│   │   └── comparar_experimentos.ipynb
│   ├── resultados/                  — métricas y figuras de todos los experimentos
│   │   ├── v1_pcn/ … v7_fb_obj_sn_ft2f/
│   │   └── comparativa_experimentos2.csv
│   └── scripts roturas/
│       ├── generar_roturas_centradas.ipynb
│       └── preprocesar_fantastic_breaks.py
│
├── E4+++++/Notebooks/               ← STL watertight
│   ├── reparar_stl.ipynb            — pipeline malla → STL imprimible
│   └── pipeline_demo.ipynb          — demo completo E2→E3→E4
│
├── E5+++++/                         ← Demo app y resultados reales
│   ├── app_pipeline_demo.ipynb      — notebook integración completo
│   ├── convertir_voxels_a_nube.py   — conversión voxel 32³ → nube (2048,3)
│   ├── Taza rota 1/2/3/             — fotos reales usadas en la demo
│   └── Resultados EJEC5/6/          — capturas de la app funcionando
│
├── Latex+++++/                      ← Memoria del TFM (LaTeX)
│   ├── memoria_tfm.tex              — documento completo
│   ├── referencias.bib              — 19 referencias bibliográficas
│   └── imagenes/                    — figuras de la memoria
│
├── Scripts+++++/                    ← Scripts de datos y figuras
│   ├── convertir_voxels_a_nube.py   — conversión E2→E3
│   ├── generar_roturas_sinteticas.py
│   ├── filtrar_normalizar_shapenet.py / _tazas.py
│   ├── descargar_fantastic_breaks.py / descargar_tazas.py
│   ├── comparar_experimentos.py
│   ├── visualizar_datos.py
│   ├── generar_figura_experimentos.py
│   └── generar_figura_representaciones.py
│
├── Documentacion/
│   ├── TFM_11_Contratos_Interfaz.md — contratos de formato entre etapas
│   └── TFM_Diagrama_Pipeline.png
│
├── NOTAS_Y_HALLAZGOS.md             — bitácora técnica completa (H1–H32+)
├── PLANIFICACION.md                 — historial de tareas y avance
└── Latex+++++/memoria_tfm.tex       — memoria completa del TFM
```

> **Datos:** no están en Git. Están en Google Drive (shapenet_limpias/, objaverse_limpias/, fantastic_breaks_procesado/, checkpoints E2 y E3).

---

## Resultados principales

### E2 — Reconstrucción (Pix2Vox++)

| Experimento | Categorías | Vistas | Resultado |
|-------------|-----------|--------|-----------|
| exp13 | 7 categorías | 5 vistas | Mejor generalización |
| exp14 | 6 categorías | 5 vistas | Mejor con tazas rotas |
| fine-tuning final | tazas rotas reales | 1–20 vistas | Demo funcional |

### E3 — Reparación de nubes de puntos

| Modelo | Datos train | CD ↓ | F-Score ↑ | Épocas |
|--------|------------|------|-----------|--------|
| PCN v3 | FB v1 | 0.0665 | 0.024 | 300 |
| PCN v4 | FB v2 | 0.0641 | 0.0236 | 480 |
| PCN v5 | FB v2 + fix centroide | 0.0630 | 0.0257 | 445 |
| PoinTr v5_obj | Obj v2 | 0.0306 | 0.270 | 490 |
| **PoinTr v6_obj_sn** | **Obj+SN** | **0.0245** | **0.4547** | **486** |
| PoinTr v7 | Obj+SN+FB ft | — | — | fine-tune |

### E4 — STL watertight

Poisson reconstruction (depth=7–10) + pymeshlab fallback. 6 objetos de prueba validados.

---

## Cómo ejecutar la demo

### Opción A — App Gradio completa (Colab)

```
1. Abrir APP+++++/colab_run_app.ipynb en Google Colab
2. Montar Drive con los checkpoints en las rutas indicadas
3. Ejecutar todas las celdas → se lanza la app en una URL pública de Colab
4. Subir fotos de un objeto roto → obtener STL
```

### Opción B — Notebook integración (Colab)

```
Abrir E5+++++/app_pipeline_demo.ipynb → sigue las instrucciones de cada sección
```

### Opción C — Solo E3 (inferencia con checkpoint)

```python
# En Colab, con el checkpoint best.pt de Drive montado:
from E3.notebooks.evaluate import evaluar_modelo
evaluar_modelo("ruta/al/best.pt", "ruta/a/nube_rota.npy")
```

---

## Datasets utilizados

| Dataset | Estado | Modelos/pares | Uso |
|---------|--------|---------------|-----|
| ShapeNet (mug·bowl·bottle·jar·can) | ✅ Procesado | 2.170 `.ply` normalizados | E2+E3 entrenamiento |
| Objaverse (vasijas) | ✅ Procesado | 197 `.ply` normalizados | E2+E3 complemento |
| Fantastic Breaks | ✅ Procesado | 61 pares vasija (2.048 pts) | E3 entrenamiento |
| Roturas sintéticas v2 | ✅ Generado | 2.299 pares | E3 entrenamiento extra |
| CO3D | ⏸ Pospuesto a P1 | — | Fotos reales (150 GB) |

Scripts de descarga en `Scripts+++++/`.

---

## Documentación técnica

| Documento | Contenido |
|-----------|-----------|
| `NOTAS_Y_HALLAZGOS.md` | Decisiones técnicas, bugs encontrados (H1–H32+), experimentos |
| `Documentacion/TFM_11_Contratos_Interfaz.md` | Formato exacto de datos entre etapas |
| `Latex+++++/memoria_tfm.tex` | Memoria completa del TFM (LaTeX/Overleaf) |
| `PLANIFICACION.md` | Historial de tareas completadas |
