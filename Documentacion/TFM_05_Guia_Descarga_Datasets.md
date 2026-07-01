# Guía de descarga de datasets + elección de categoría

> Cómo conseguir cada base de datos y qué categoría usar.
> **Categoría elegida para empezar: TAZAS (mugs / cups)** — revisable más adelante.
> Raquel Roca · Junio 2026

---

## 0. Decisión: empezamos con TAZAS

El grupo empieza probando con la categoría **tazas** (mugs/cups) y, según resultados, se podrá cambiar. Es una elección muy sólida para arrancar (ver el porqué en la sección 1).

> Nada de lo construido se pierde si luego se cambia de categoría: el pipeline es el mismo; solo cambian los datos de entrada.

---

## 1. Por qué las tazas son una buena categoría

- **Existen en los cuatro datasets relevantes** → se pueden combinar para entrenar, reparar y validar.
- **Coinciden con Fantastic Breaks** (que es básicamente menaje/cerámica) → permite usar **roturas reales** en la etapa 3, no solo sintéticas.
- **Geometría amable** (mate, con textura, formas simples) → se reconstruyen bien.
- **El asa es un objetivo de reparación ideal**: romper y reconstruir el asa de una taza es un caso de completado muy visual para la defensa.
- **Historia redonda:** "reconstruimos y reparamos vajilla/cerámica rota a partir de fotos".

---

## 2. Mejores categorías por dataset (referencia para decidir)

| Dataset | Mejores categorías | Notas |
|---------|--------------------|-------|
| **ABO** (curado, limpio) | sillas, mesas, lámparas, jarrones/macetas, sofás | Mobiliario; tazas escasas. Muy bueno para sillas |
| **Objaverse** (enorme, variado) | jarrón, **taza (mug)**, bol, botella, tetera, silla | Muchos ejemplos; calidad desigual (filtrar) |
| **CO3D** (fotos reales) | **cup (taza)**, vase, bowl, chair, bottle, plant | 50 categorías reales con fotos y poses |
| **Fantastic Breaks** (roto↔completo real) | **tazas, boles, platos, jarras, vasijas** | Menaje y cerámica. NO tiene muebles |
| **Thingi10K** (imprimibilidad) | *cualquiera* | Pozo de mallas imprimibles para validar la etapa 4 |

**Categorías que aparecen en casi todos:** tazas, jarrones y boles. Por eso son las mejores apuestas. (Las sillas son geniales para reconstrucción pero **no están en Fantastic Breaks**, así que no permiten roturas reales.)

---

## 3. Qué datasets usar para TAZAS

| Para qué | Dataset | Categoría / ID | Acceso |
|----------|---------|----------------|--------|
| Entrenar reconstrucción + reparación (principal) | **Objaverse** | `mug` (vía LVIS) | Inmediato |
| Datos reales roto↔completo (etapa 3) | **Fantastic Breaks** | clase tazas/mugs | Formulario |
| Fotos reales (extensión P1) | **CO3D** | `cup` | Inmediato |
| Validar imprimibilidad (etapa 4) | **Thingi10K** | — | `pip` |
| Comparación estándar (si llega acceso) | **ShapeNet** | `03797390` (mug, 214 modelos) | Registro (~1 día) |
| Plan B mientras se aprueba ShapeNet | **ABO** | drinkware (escaso) | Inmediato |

---

## 4. Cómo descargar cada uno (con tazas)

### 4.1 Objaverse — principal, inmediato

```python
!pip install objaverse
import objaverse

lvis = objaverse.load_lvis_annotations()

# Ver qué categorías de tazas hay disponibles
print([k for k in lvis if 'mug' in k or 'cup' in k])

# Descargar un subconjunto de tazas
ids = lvis["mug"]
print("Tazas disponibles:", len(ids))
objetos = objaverse.load_objects(uids=ids[:200])   # baja 200 para empezar
print("Descargadas:", len(objetos))
```

### 4.2 Fantastic Breaks — roturas reales (etapa 3)

1. Entra en `https://terascale-all-sensing-research-studio.github.io/FantasticBreaks/`
2. Rellena el formulario de descarga y obtén el enlace (suele ser Google Drive).
3. En Colab:

```python
!pip install gdown
!gdown "ID_O_ENLACE_QUE_TE_DEN"
```

4. Quédate con los objetos de clase **taza/mug** (filtrando por la etiqueta de clase del dataset).

### 4.3 CO3D — fotos reales (solo extensión P1)

```python
!git clone https://github.com/facebookresearch/co3d.git
%cd co3d
!pip install -e .
# Descargar SOLO la categoría 'cup' (necesitas el archivo de enlaces de la web de CO3D)
!python ./co3d/download_dataset.py --download_folder DATOS_CO3D \
        --link_list_file links.txt --download_categories cup
```

### 4.4 Thingi10K — imprimibilidad (etapa 4)

```python
!pip install thingi10k
import thingi10k
thingi10k.init()       # descarga y cachea (la 1ª vez tarda)

for entry in thingi10k.dataset():
    vertices, caras = thingi10k.load_file(entry['file_path'])
    break
```

### 4.5 ShapeNet — si os dan acceso (comparación estándar)

1. Solicita acceso en `https://huggingface.co/datasets/ShapeNet/ShapeNetCore` (nombre, tutor/PI, institución; usar correo UCM).
2. Crea un token en HF (*Settings → Access Tokens*).
3. Descarga solo el synset de tazas (`03797390`):

```python
!pip install huggingface_hub
from huggingface_hub import login, hf_hub_download
login("TU_TOKEN")

ruta = hf_hub_download(repo_id="ShapeNet/ShapeNetCore",
                       filename="03797390.zip",     # 03797390 = mug
                       repo_type="dataset",
                       local_dir="shapenet")
print("Descargado:", ruta)
```

### 4.6 ABO — plan B mientras se aprueba ShapeNet

```python
!wget https://amazon-berkeley-objects.s3.amazonaws.com/archives/abo-3dmodels.tar
!tar -xf abo-3dmodels.tar
```
> Las tazas escasean en ABO (es muy de mobiliario). Útil como alternativa general, pero para tazas es mejor **Objaverse**.

---

## 5. Plan de acción y avisos

**Orden recomendado:**
1. **Ya:** descargar tazas de **Objaverse** y empezar a trastear.
2. Pedir/descargar **Fantastic Breaks** (formulario) para tener roturas reales de tazas.
3. **Thingi10K** con `pip` al llegar a la etapa 4.
4. **CO3D (cup)** solo si dais el salto a fotos reales (P1).
5. **ShapeNet (03797390)** cuando os aprueben, para comparar con benchmarks.

**Avisos prácticos:**
- En Colab el **disco es temporal y limitado**: baja solo un **subconjunto** (p. ej. 200 modelos), no todo.
- Para que los datos **persistan entre sesiones**, monta Google Drive y guarda ahí:
```python
from google.colab import drive
drive.mount('/content/drive')
```
- **No hace falta ShapeNet** para que el TFM funcione: con Objaverse + Fantastic Breaks (+ CO3D/Thingi10K) está todo cubierto. ShapeNet solo facilita comparar con otros papers.
- Los **nombres de categoría** varían entre datasets (CO3D usa `cup`, Objaverse `mug`); por eso en Objaverse conviene imprimir primero las claves disponibles (ver 4.1).
- Fantastic Breaks es **pequeño** (~150 objetos en total): úsalo como **test/validación con roturas reales**, y entrena con roturas **sintéticas** sobre Objaverse.

---

## 6. Categorías de ShapeNet (referencia completa)

Las 55 categorías de ShapeNetCore con sus synset IDs. Las marcadas con `<-- vasija` son las relevantes para el TFM.

| Synset ID | Categoría | Nota |
|-----------|-----------|------|
| 02691156 | airplane (avión) | |
| 02747177 | trash bin (cubo basura) | |
| 02773838 | bag (bolso) | |
| 02801938 | basket (cesta) | |
| 02808440 | bathtub (bañera) | |
| 02818832 | bed (cama) | |
| 02828884 | bench (banco) | |
| 02843684 | birdhouse (casita pájaro) | |
| 02871439 | bookshelf (estantería) | |
| 02876657 | bottle (botella) | **vasija** |
| 02880940 | bowl (cuenco) | **vasija** |
| 02924116 | bus (autobús) | |
| 02933112 | cabinet (armario) | |
| 02942699 | camera (cámara) | |
| 02946921 | can (lata) | |
| 02954340 | cap (gorra) | |
| 02958343 | car (coche) | |
| 02992529 | cellphone (móvil) | |
| 03001627 | chair (silla) | |
| 03046257 | clock (reloj) | |
| 03085013 | keyboard (teclado) | |
| 03207941 | dishwasher (lavavajillas) | |
| 03211117 | monitor (pantalla) | |
| 03261776 | earphone (auricular) | |
| 03325088 | faucet (grifo) | |
| 03337140 | file cabinet (archivador) | |
| 03467517 | guitar (guitarra) | |
| 03513137 | helmet (casco) | industrial |
| 03593526 | jar (tarro) | **vasija** |
| 03624134 | knife (cuchillo) | |
| 03636649 | lamp (lámpara) | |
| 03642806 | laptop (portátil) | |
| 03691459 | loudspeaker (altavoz) | |
| 03710193 | mailbox (buzón) | |
| 03759954 | microphone (micrófono) | |
| 03761084 | microwave (microondas) | |
| 03790512 | motorbike (moto) | |
| 03797390 | mug (taza) | **vasija** |
| 03928116 | piano (piano) | |
| 03938244 | pillow (almohada) | |
| 03948459 | pistol (pistola) | |
| 03991062 | flowerpot (maceta) | **vasija** |
| 04004475 | printer (impresora) | |
| 04074963 | remote control (mando) | |
| 04090263 | rifle (rifle) | |
| 04099429 | rocket (cohete) | |
| 04225987 | skateboard (patinete) | |
| 04256520 | sofa (sofá) | |
| 04330267 | stove (cocina/horno) | |
| 04379243 | table (mesa) | |
| 04401088 | telephone (teléfono) | |
| 04460130 | tower (torre) | |
| 04468005 | train (tren) | |
| 04530566 | watercraft (barco) | |
| 04554684 | washer (lavadora) | |

**Synsets P0:** mug `03797390` · bowl `02880940` · bottle `02876657` · jar `03593526` · can `02946921`
**Opcional:** flowerpot `03991062` (misma topología, fácil de añadir si conviene más volumen)
