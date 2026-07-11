# TFM_12 — Datos preprocesados para E3 (Reparación)

> Documento de entrega de Raquel → Rocío.
> Describe exactamente qué datos hay listos, en qué formato están, y cómo ampliarlos.
> Raquel Roca · 11 jul 2026.

---

## Qué hay listo

En la carpeta Drive del grupo (`fantastic_breaks_procesado/`) hay **122 archivos `.npy`**
que forman **61 pares (roto, completo)** listos para entrenar el modelo de reparación E3.

Peso total: ~3 MB. No necesitas descargar los 8 GB del dataset raw para empezar.

---

## Origen de los datos

Los datos vienen de **Fantastic Breaks** (Lamb et al., CVPR 2023): el único dataset público
con objetos físicamente rotos emparejados con su versión completa. Son escaneos 3D reales,
no modelos sintéticos.

Cada par original tiene ~1.2 millones de puntos por archivo `.ply`. El preprocesado los
reduce a 2.048 puntos, que es el estándar de los papers de shape completion (PoinTr, PCN,
SnowFlakeNet). Si el modelo que eliges necesita otro número (p.ej. 8.192), el script se
puede relanzar con `--n_puntos 8192` y regenera todo en minutos.

---

## Formato exacto de cada archivo

```
Datos/fantastic_breaks/procesado/
├── 00_00002_roto.npy       <- numpy array float32, shape (2048, 3)
├── 00_00002_completo.npy   <- numpy array float32, shape (2048, 3)
├── 00_00003_roto.npy
├── 00_00003_completo.npy
└── ... (122 archivos en total)
```

**Nombre:** `<clase>_<objeto>_<tipo>.npy`
- `clase`: número de carpeta del dataset (00=mug, 02=bowl, 03=jar, 05=cup)
- `objeto`: ID del objeto dentro de la clase (p.ej. `00002`)
- `tipo`: `roto` (entrada al modelo) o `completo` (target, lo que el modelo debe predecir)

**Contenido de cada array:**
- Dtype: `float32`
- Shape: `(2048, 3)` → 2.048 puntos, coordenadas XYZ
- Normalización: centrado en el origen, escalado a esfera unidad (radio máximo = 1)

**Cómo cargarlo en PyTorch:**

```python
import numpy as np
import torch

roto     = torch.from_numpy(np.load("00_00002_roto.npy"))      # (2048, 3)
completo = torch.from_numpy(np.load("00_00002_completo.npy"))  # (2048, 3)
```

---

## Qué clases hay y cuántos pares

| Clase | Nombre | Pares |
|-------|--------|-------|
| 00    | mug (taza con asa) | 30 |
| 02    | bowl (cuenco) | 17 |
| 03    | jar (tarro) | 6 |
| 05    | cup (taza sin asa) | 8 |
| **Total** | **vasijas** | **61** |

> **Nota importante:** en documentación anterior las clases 03 y 05 estaban intercambiadas.
> El mapping correcto (verificado contra la Tabla 1 del paper) es 03=jar y 05=cup.
> Los archivos `.npy` generados son correctos — la etiqueta está en el nombre del archivo.

---

## Cómo ampliar los datos si 61 pares no son suficientes

El dataset tiene 150 pares en total. El script acepta un argumento `--clases` para incluir
más categorías. Se pueden añadir sin tocar los archivos ya generados (el script no
sobreescribe, añade).

### Opción A — Añadir plates (35 pares más → total 96)

```bash
python Scripts/preprocesar_fantastic_breaks.py --clases vasijas,plate
```

Los plates son platos/vajilla plana. Se rompen de forma diferente a las vasijas (fractura
en plano) pero el task de shape completion es el mismo. Aumenta mucho el volumen.

### Opción B — Añadir statues (30 pares más → total 91)

```bash
python Scripts/preprocesar_fantastic_breaks.py --clases vasijas,statue
```

Las statues son figuras/esculturas con geometría freeform compleja. Útil si el modelo
necesita aprender formas más variadas para generalizar mejor.

### Opción C — Usar todo el dataset (150 pares)

```bash
python Scripts/preprocesar_fantastic_breaks.py --clases todas
```

Incluye también box, coaster, misc y otras categorías con pocos ejemplos (2-6 pares).
Solo recomendable si se entrena un modelo general de shape completion, no uno especializado
en vasijas.

### Otras opciones del script

```bash
# Cambiar número de puntos (p.ej. para modelos que usan 8.192)
python Scripts/preprocesar_fantastic_breaks.py --n_puntos 8192

# Ver qué haría sin escribir nada
python Scripts/preprocesar_fantastic_breaks.py --dry-run --clases todas

# Directorio de salida alternativo
python Scripts/preprocesar_fantastic_breaks.py --destino Datos/fantastic_breaks/procesado_8k
```

---

## Ampliación con otros datasets

Fantastic Breaks solo tiene 150 pares en total. Para augmentation sintética de roturas
hay otras opciones:

| Dataset | Qué da | Estado |
|---------|--------|--------|
| **ShapeNet** (2.170 modelos limpios) | Vasijas completas. Se pueden "romper" sintéticamente con planos de corte aleatorios para generar pares (roto, completo) adicionales | Listo en `Datos/shapenet/limpias/` |
| **Objaverse** (197 modelos limpios) | Vasijas completas, menos calidad que ShapeNet pero más variedad | Listo en `Datos/objaverse/limpias/` |
| **ModelNet40** (163 modelos watertight) | cup+bowl watertight, ideal para pares sintéticos porque los modelos son sólidos cerrados | Pendiente de descargar (~500 MB) |

La augmentación sintética (cortar modelos completos con un plano aleatorio para simular
una rotura) es la forma estándar de ampliar datos para shape completion cuando el dataset
de roturas reales es pequeño. Está en el radar para agosto si los 61 pares reales no
son suficientes para que el modelo converja.

---

## El script de preprocesado

Está en `Scripts/preprocesar_fantastic_breaks.py`. Usa trimesh (ya instalado).
No depende de open3d (que no tiene build para Python 3.14).

```bash
# Uso por defecto (61 pares vasija)
python Scripts/preprocesar_fantastic_breaks.py

# Ver todas las opciones
python Scripts/preprocesar_fantastic_breaks.py --help
```
