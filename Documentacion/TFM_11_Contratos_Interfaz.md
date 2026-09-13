# TFM_11 — Contratos de interfaz entre etapas

> Raquel Roca · Junio 2026 · **Actualizado 13 sep 2026 con decisiones finales.**
> Todos los contratos están cerrados y en producción en la app REBUILD3D.

---

## Convenciones generales del proyecto

- **Unidades:** metros. **Escala:** centrado en origen, esfera unidad (radio máximo = 1).
- **Sistema de coordenadas:** Y arriba, centrado en el origen.
- **Categoría de trabajo:** vasijas (mug, bowl, bottle/vase, jar, can).
- **Puntos por nube:** 2.048 (estándar PoinTr/PCN).

---

## Contrato E1 → E2  (Captura/preproceso → Reconstrucción)

**Decisión final:** E1 está integrado en `pipeline_e2.py` como `preparar_imagen()`. No hay carpeta E1 separada.

| Campo | Formato final |
|-------|--------------|
| Imágenes | JPG, cualquier resolución (se redimensionan internamente a 224×224) |
| Fondo | Eliminado por alpha compositing (canal alfa del PNG) |
| Nº de vistas | **5 ángulos fijos**: frontal (0°), trasera-izquierda (225°), lateral derecho alto (90°+40°), lateral izquierdo alto (270°+40°), cenital (~60°) |
| Poses de cámara | **No se entregan** — Pix2Vox++ usa ángulos fijos, no necesita COLMAP |
| Estructura | 5 imágenes pasadas directamente como lista a `fotos_a_nube()` |

> ~~SAM + COLMAP~~ descartados en P0. Alpha compositing + 5 ángulos fijos es suficiente para la demo.

---

## Contrato E2 → E3  (Reconstrucción → Reparación)

**Formato cerrado el 11 jul 2026. En producción.**

| Campo | Formato acordado |
|-------|-----------------|
| Geometría | nube de puntos `.npy`, array float32 shape **(2048, 3)** |
| Coordenadas | XYZ en metros, sin normales |
| Normalización | centrada en origen, escalada a esfera unidad (radio máximo = 1) |
| Estado | nube **incompleta** (parte rota / huecos) — entrada al modelo de reparación |
| Conversión | voxel grid 32³ de Pix2Vox++ → nube 2.048 pts con FPS (`convertir_voxels_a_nube.py`) |

**Cómo cargarlo:**
```python
import numpy as np, torch
nube_rota = torch.from_numpy(np.load("objeto_roto.npy"))  # (2048, 3)
```

**Cómo generarlo desde voxels Pix2Vox++:**
```python
from Scripts.convertir_voxels_a_nube import voxels_a_nube
nube = voxels_a_nube(voxel_grid_32)  # → numpy (2048, 3)
```

---

## Contrato E3 → E4  (Reparación → STL imprimible)

**Decisión final:** E3 entrega una **nube de puntos completa** (no malla). E4 hace la reconstrucción de malla.

| Campo | Formato final |
|-------|--------------|
| Geometría | nube de puntos `.npy`, array float32 **(2048, 3)** completa (sin huecos) |
| Normalización | igual que la entrada: centrada en origen, esfera unidad |
| Proceso en E4 | Poisson reconstruction (depth=7–10) → malla → watertight |

---

## Contrato E4 → E5  (STL imprimible → App)

| Campo | Formato acordado |
|-------|-----------------|
| Fichero | `.STL` **watertight**, validado, listo para laminador |
| Escala física | mm reales (el usuario decide tamaño de impresión) |

---

## Tabla resumen

```
E1 ──[5 JPGs, ángulos fijos, alpha compositing]──────────────────────────── integrado en E2
E2 ──[nube .npy float32 (2048,3), centrada, esfera unidad, incompleta]────► E3
E3 ──[nube .npy float32 (2048,3), centrada, esfera unidad, completa]──────► E4
E4 ──[.STL watertight]────────────────────────────────────────────────────► E5 (app Gradio)
```

---

## Decisiones cerradas

- [x] **E1:** 5 ángulos fijos, alpha compositing — sin SAM ni COLMAP
- [x] **E2:** Pix2Vox++ (multi-vista → voxel 32³ → nube 2.048 pts)
- [x] **E2→E3:** nube de puntos numpy float32 (2048, 3)
- [x] **E3→E4:** nube de puntos completa numpy float32 (2048, 3) → Poisson en E4
- [x] **E4→E5:** `.STL` watertight
- [x] **Salidas intermedias:** Google Drive (checkpoints E2 y E3)
