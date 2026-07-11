# TFM_11 — Contratos de interfaz entre etapas

> El acuerdo más crítico del proyecto: qué formato EXACTO pasa de una etapa a la
> siguiente. Si esto no está cerrado, la integración falla aunque cada módulo
> funcione por separado. Raquel Roca · Junio 2026.

---

## Por qué esto es lo primero

Cada persona desarrolla su etapa en paralelo. Para que encajen al final, la salida
de una etapa debe ser **exactamente** la entrada que espera la siguiente. Estos
contratos se acuerdan AHORA (era el hito del 21 jun) y se congelan. Cambiar un
contrato después obliga a avisar a las dos etapas afectadas.

Convención general del proyecto:
- **Unidades:** metros. **Escala:** objeto normalizado a caja unidad (lado 1).
- **Sistema de coordenadas:** Y arriba, centrado en el origen (mismo criterio que
  `tazas_limpias`).
- **Categoría de trabajo:** vasijas (mug, bowl, bottle/vase, jar).

---

## Contrato E1 → E2  (Captura/preproceso → Reconstrucción)

**La etapa 1 entrega a la 2:**

| Campo | Formato acordado (P0) |
|-------|-----------------------|
| Imágenes | PNG/JPG, **256×256** (o 512×512: ¡decidir!), recortadas al objeto |
| Fondo | **blanco** en P0 / eliminado con SAM en P1 |
| Nº de vistas | mínimo acordado (ej. 8-12 alrededor del objeto) |
| Poses de cámara | ¿se entregan? (sí si E2 usa NeRF/COLMAP; no si usa image-to-3D feed-forward) |
| Estructura | una carpeta por objeto: `objeto_XXXX/img_000.png ... + poses.json` |

> ⚠️ Decisión clave que condiciona todo E2: **¿método con poses (nerfacto/COLMAP) o
> sin poses (Zero123/LRM)?** De eso depende si E1 debe estimar pose de cámara.

---

## Contrato E2 → E3  (Reconstrucción → Reparación)

**La etapa 2 entrega a la 3:**

| Campo | Formato acordado |
|-------|------------------|
| Geometría | nube de puntos `.npy`, array float32 shape **(2048, 3)** |
| Coordenadas | XYZ en metros, sin normales |
| Normalización | centrada en origen, escalada a esfera unidad (radio máximo = 1) |
| Estado | nube **incompleta** (parte rota / huecos) — es la entrada al modelo |
| Metadatos | `info.json`: nº puntos, bounding box, método de E2 usado |

> **Formato confirmado el 11 jul 2026** a partir de los datos de entrenamiento de E3.
> Fantastics Breaks procesado usa este mismo formato: 2.048 puntos, float32, (2048,3).
> Si el modelo de Rocío necesita otro nº de puntos, avisar a Raquel para regenerar.

**Cómo cargarlo:**
```python
import numpy as np, torch
nube_rota = torch.from_numpy(np.load("objeto_roto.npy"))  # (2048, 3)
```

---

## Contrato E3 → E4  (Reparación → STL imprimible)

**La etapa 3 entrega a la 4:**

| Campo | Formato acordado |
|-------|------------------|
| Geometría | malla completa `.obj`/`.ply` (ya sin huecos grandes) |
| Garantía | topología cerrada *en lo posible* (E4 termina de hacerla watertight) |
| Metadatos | `info.json`: si era objeto roto, IoU/Chamfer de la reparación |

---

## Contrato E4 → E5  (STL imprimible → App)

**La etapa 4 entrega a la 5:**

| Campo | Formato acordado |
|-------|------------------|
| Fichero | `.STL` **watertight**, validado, listo para laminador |
| Validación | `report.json`: watertight sí/no, nº de errores reparados, volumen |
| Escala física | mm reales (la app/usuario decide tamaño de impresión) |

---

## Tabla resumen (para pegar en una pizarra)

```
E1 --[imágenes 256² fondo blanco (+poses?)]--> E2
E2 --[nube .ply 2048 pts normalizada, puede tener huecos]--> E3
E3 --[malla .obj completa]--> E4
E4 --[.STL watertight + report.json]--> E5
```

---

## Decisiones pendientes de cerrar (rellenar en la reunión)

- [ ] Resolución de imagen de E1: **256² o 512²**.
- [ ] Método de E2: **con poses (nerfacto/COLMAP)** o **sin poses (Zero123/LRM)**.
      → determina si E1 entrega `poses.json`.
- [ ] Representación E2→E3: **nube de puntos** o **malla** (y nº de puntos si nube).
- [ ] Nombre y esquema exactos de los `info.json` / `report.json`.
- [ ] Dónde se guardan las salidas intermedias compartidas (HF/Drive).
