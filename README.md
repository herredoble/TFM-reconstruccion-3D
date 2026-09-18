# TFM — Reconstrucción y reparación 3D de objetos rotos

De fotos de un objeto roto → nube de puntos reconstruida → malla reparada → archivo STL imprimible.

**Equipo:** Raquel Roca · Rocío · Álvaro · Almu · Luis  
**Estado:** ✅ Entregado 15 septiembre 2026  
**Última actualización:** 18 septiembre 2026

> **Datos y checkpoints:** no están en Git por tamaño.  
> → [Carpeta Google Drive del proyecto](https://drive.google.com/drive/folders/1lj-uBjD3ZL-hETWJynR98AtWe2PUdQtD?usp=drive_link)

---

## Pipeline completo

```
[Fotos JPG]
    ↓ E2   Pix2Vox++ (reconstrucción voxel 32³ → nube 2048 pts)
[Nube de puntos rota · numpy (2048,3)]
    ↓ E3   PoinTr / PCN (shape completion)
[Nube completa · numpy (2048,3)]
    ↓ E4   Poisson reconstruction → malla .STL
[Malla .STL]
    ↓ APP  Gradio app (REBUILD3D)
[Demo interactiva end-to-end]
```

**Mejor resultado E3:** PoinTr v6_obj_sn · CD = 0.0245 · F-Score = 0.4547  
**Demo funcional:** app Gradio con fotos reales de tazas rotas → STL en ~90s (A100)

---

## Estructura del repositorio

```
TFM-reconstruccion-3D/
│
├── E2_reconstruccion/               ← Reconstrucción 3D (Pix2Vox++)
│   ├── [FINAL] Fine tuning PIx2Vox Rotas.ipynb
│   ├── [FINAL] Evaluacion_Tazas_Rotas.ipynb
│   ├── [FINAL] Pix2vox++_Ampliado.ipynb
│   ├── modelo_pix2vox.py            — arquitectura Pix2Vox++
│   └── checkpoints/                 — pesos (.pth — en Drive)
│
├── E3_reparacion/                   ← Reparación de nubes de puntos
│   ├── notebooks/                   — entrenamiento PCN y PoinTr (v1→v6)
│   ├── resultados/                  — métricas y figuras por experimento
│   ├── comparativa_experimentos2.csv
│   └── scripts roturas/             — generación de roturas sintéticas
│
├── E4_stl/Notebooks/                ← Conversión nube → STL
│   ├── reparar_stl_EJEC3.ipynb      — pipeline reparación + Poisson
│   └── pipeline_demo_EJEC5.ipynb    — demo completo E2→E3→E4
│
├── E5_demo/                         ← App demo y resultados reales
│   ├── app_pipeline_demo.ipynb      — notebook integración completo
│   ├── convertir_voxels_a_nube.py   — conversión voxel 32³ → nube (2048,3)
│   ├── Entradas APP/                — fotos tazas rotas + .npy de demo
│   ├── Resultados EJEC5/            — capturas pipeline desde fotos
│   └── Resultados EJEC6 desde .npy/ — capturas pipeline desde .npy
│
├── Latex/                           ← Memoria del TFM (LaTeX)
│   ├── memoria_tfm.tex              — documento completo
│   ├── referencias.bib              — referencias bibliográficas
│   └── imagenes/                    — figuras de la memoria
│
├── Scripts/                         ← Scripts de datos y figuras
│   ├── convertir_voxels_a_nube.py
│   ├── generar_roturas_sinteticas.py
│   ├── filtrar_normalizar_shapenet.py
│   ├── descargar_fantastic_breaks.py
│   ├── generar_figura_experimentos.py
│   ├── generar_figura_representaciones.py
│   └── generar_gantt_anexo.py
│
└── Documentacion/
    ├── TFM_11_Contratos_Interfaz.md — contratos de formato entre etapas
    └── TFM_Diagrama_Pipeline.png
```

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
| PCN v4 | FB v2 | 0.0641 | 0.0236 | 480 |
| PCN v5 | FB v2 + fix centroide | 0.0630 | 0.0257 | 445 |
| PoinTr v5_obj | Objaverse v2 | 0.0306 | 0.270 | 490 |
| **PoinTr v6_obj_sn** | **Objaverse + ShapeNet** | **0.0245** | **0.4547** | **486** |

### E4 — Conversión a STL

Poisson Surface Reconstruction (depth=7–10) + pymeshlab + trimesh. La densidad de la nube de entrada (2048 pts, espaciado ~0.056 u) limita la calidad de la malla; los resultados son visuales pero no watertight para impresión directa.

---

## Cómo ejecutar la demo

### App Gradio completa (Colab + Drive)

```
1. Montar Drive con checkpoints en las rutas indicadas
2. Abrir E5_demo/app_pipeline_demo.ipynb en Google Colab (GPU A100)
3. Ejecutar todas las celdas → app disponible en URL pública de Colab
4. Subir 5 fotos de un objeto roto → obtener STL en ~90s
```

### Solo E3 — inferencia con checkpoint

```python
# En Colab, con best.pt de Drive montado:
from E3_reparacion.notebooks.evaluate import evaluar_modelo
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

Scripts de descarga en `Scripts/`. Datos en [Google Drive](https://drive.google.com/drive/folders/1lj-uBjD3ZL-hETWJynR98AtWe2PUdQtD?usp=drive_link).
