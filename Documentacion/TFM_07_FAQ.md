# Preguntas frecuentes (FAQ) del TFM — Reconstrucción 3D

> Documento vivo donde se recogen las dudas que van surgiendo y sus respuestas.
> Complementa la *Guía completa* y el *Tutorial práctico*.
> Raquel Roca · Junio 2026

---

## FAQ 1 — ¿Cómo consigo imágenes de una categoría concreta de objetos? ¿Puedo filtrar los datasets?

**Sí, se puede filtrar, y además es lo recomendable.** Casi todos los datasets ya vienen **organizados o etiquetados por categoría**, así que quedarse solo con un tipo de objeto es fácil.

### Primero, un matiz: datasets de objetos 3D vs. imágenes
Los datasets que se manejan (ShapeNet, Objaverse...) son de **objetos 3D** (mallas), no de fotos. Para obtener **imágenes** de tu categoría hay dos vías:

1. **Imágenes sintéticas:** coges los modelos 3D de tu categoría y los "fotografías" virtualmente desde varios ángulos (renderizado con Blender). Es lo más cómodo para empezar y ya conoces la forma real (ground truth).
2. **Fotos reales:** usas un dataset que ya contiene fotos reales por categoría, como **CO3D**.

### Cómo se filtra en cada dataset

| Dataset | Cómo está organizado | Cómo filtras una categoría |
|---------|----------------------|----------------------------|
| **ShapeNet** | Carpetas por categoría con un ID (synset). Ej.: sillas = `03001627`, mesas = `04379243`, aviones = `02691156`, coches = `02958343` | Descargas/usas solo esa carpeta. Trivial |
| **Objaverse** | Anotaciones de categoría (LVIS) | Con su librería de Python pides solo los objetos de tu categoría (ver código) |
| **CO3D** | 50 categorías reales (silla, mochila, taza, plátano...), cada una en su carpeta | Eliges solo las carpetas de tu categoría. Son fotos reales |
| **ABO** | Metadatos con "product type" | Filtras por tipo de producto |
| **Fantastic Breaks** | Etiqueta de clase y material por objeto | Filtras por la etiqueta de clase |

### Ejemplo de filtrado en Objaverse (Python)

```python
import objaverse

# 1) Cargar las anotaciones de categoría (LVIS)
lvis = objaverse.load_lvis_annotations()   # dict: categoría -> lista de IDs

# 2) Quedarte solo con los objetos de TU categoría, p. ej. "vase" (jarrón)
ids_jarrones = lvis["vase"]
print("Jarrones disponibles:", len(ids_jarrones))

# 3) Descargar SOLO esos objetos (no los 800.000)
objetos = objaverse.load_objects(uids=ids_jarrones)
```

En **ShapeNet** ni siquiera hace falta código: te bajas únicamente la carpeta del synset de tu categoría.

> **Resumen:** no hay que usar el dataset entero. Coges solo tu categoría y, si vas por imágenes sintéticas, renderizas fotos solo de esos modelos.

---

## FAQ 2 — ¿Afecta mucho usar todos los tipos de objetos en vez de centrarse en una categoría?

**Sí, afecta mucho, y centrarse en una sola categoría es claramente mejor para este TFM.**

### El porqué, sin tecnicismos
Cuanto más variado es lo que la red tiene que aprender, **más datos, más potencia de cálculo (GPU) y más tiempo** necesita. Una red que solo ve jarrones aprende muy bien "cómo es un jarrón" y por eso los reconstruye y repara mucho mejor. Una red que debe aprender jarrones + sillas + coches + aviones a la vez necesita recursos enormes y, con tiempo y GPU limitados, saldría **peor en todo**.

Esto es especialmente cierto en la **etapa 3 (reparación)**: la red repara bien porque tiene un "sentido común" de la forma. Si solo conoce jarrones y falta un asa, propone un asa coherente. Un modelo generalista tiene ese sentido común mucho más diluido.

### Ventajas de centrarse en una categoría (alcance P0)
- **Mejor calidad** de resultados con los recursos disponibles.
- **Menos datos** que descargar/almacenar/entrenar (Objaverse-XL son terabytes; una categoría son megas/gigas).
- **Más fácil de evaluar y defender** ante el tutor (historia limpia: "nos especializamos en X").
- **Menos riesgo** de no llegar a la entrega.

### Cuándo tendría sentido usar varias categorías
- Solo como **extensión P1**, si el núcleo ya funciona y sobra tiempo.
- O partiendo de un **modelo grande ya preentrenado** (entrenado por terceros con todo tipo de objetos, a un coste de cómputo enorme) y haciéndole solo **fine-tuning** a vuestra categoría. Da lo mejor de ambos mundos, pero el grueso del trabajo sigue siendo sobre una categoría.

### Qué categoría elegir (importa)
Que tenga **muchos ejemplos**, geometría "amable" (mate, con textura, no transparente ni muy fina) y, a ser posible, que **exista en varios datasets** para poder cruzarlos. Buenas candidatas:
- **Sillas** — clásico; miles en ShapeNet y fotos reales en CO3D.
- **Jarrones / vasijas** — encajan perfecto con la idea de "reparar piezas rotas" y son muy visuales para la defensa.
- **Tazas / mugs** — sencillas y abundantes.

> **Veredicto:** una sola categoría para el P0. Mejor calidad, menos cómputo, más fácil de defender y menos arriesgado. Más categorías = extensión opcional al final.

---

## FAQ 3 — ¿Para qué sirven las imágenes que generamos a partir de los modelos 3D?

Para **entrenar la reconstrucción (etapa 2)**, que necesita ejemplos resueltos. La red aprende un mapeo:

**imágenes → forma 3D**

Y para enseñárselo hacen falta **pares** donde se conozca la respuesta correcta:
- **Entrada** = las imágenes (las que renderizamos desde el modelo 3D).
- **Respuesta correcta (ground truth)** = el modelo 3D real (el `.glb` de Objaverse).

Como ya tenemos el `.glb`, al "fotografiarlo" desde varios ángulos **fabricamos esos pares automáticamente y gratis**, además con las **poses de cámara perfectas** (sabemos exactamente desde dónde se tomó cada imagen, algo carísimo de obtener con fotos reales).

> **En una frase:** el render es el *ejercicio* y el `.glb` es la *solución* con la que la red corrige sus errores. Las imágenes son la entrada; el modelo 3D es el objetivo a predecir.

---

## FAQ 4 — ¿Necesitamos imágenes "con ruido" o un dataset de fotos reales? (la brecha sim-a-real)

Buena intuición: sí, hay un problema real y conocido aquí, llamado **brecha sim-a-real** (*sim-to-real gap*).

- Las imágenes renderizadas de un `.glb` salen **demasiado perfectas**: fondo limpio, luz ideal, sin sombras raras, sin desenfoque, sin grano de cámara.
- Las **fotos reales** (de un móvil) son lo contrario: fondo desordenado, sombras, movimiento, iluminación variable, poses imperfectas.
- Si se entrena solo con imágenes "de laboratorio", el modelo puede ir genial con renders y **fallar con fotos reales**.

**La solución no suele ser descargar un "dataset de imágenes con ruido" aparte**, sino **ensuciar los propios renders** durante el entrenamiento:
- **Data augmentation:** añadir a propósito ruido, desenfoque y cambios de brillo/contraste a las imágenes.
- **Domain randomization:** variar mucho el **fondo, la iluminación y los colores** en cada render para que el modelo se vuelva robusto y no dependa de un fondo limpio.

Y como **red de seguridad**, se **valida con fotos reales**: para eso está el dataset **CO3D** (fotos reales de tazas, categoría `cup`). Se entrena con renders aumentados y se comprueba con CO3D que funciona en el mundo real.

| Objetivo | Qué imágenes generar |
|----------|----------------------|
| **P0 (básico):** reconstruir desde vistas limpias | Renders limpios desde varios ángulos. Suficiente para que funcione |
| **Realista (P1):** que funcione con **fotos de móvil** | Renders + **data augmentation** (ruido, fondos, luz) + validar con **CO3D** |

> **Veredicto:** las imágenes generadas son los "ejercicios con solución" para entrenar. Añadir ruido/variación (augmentation) es el paso extra necesario **solo si** se quiere que funcione con fotos reales, no únicamente con renders.

---

---

## FAQ 5 — ¿Es viable hacer el TFM con todos los tipos de objetos en vez de centrarse en uno?

**No es viable**, y no es una cuestión de esfuerzo sino de recursos físicos y de calidad del resultado.

### Los números concretos

| Escenario | Modelos 3D | Descarga | GPU estimada para E3 | Calidad en tazas |
|-----------|-----------|----------|----------------------|-----------------|
| **Una categoría (tazas)** | ~200 | ~215 MB (ya hecho) | ~4-8h Colab T4 | Alta |
| **Vasijas (cup+mug+bowl+vase)** | ~700 | ~600 MB | ~12-24h Colab T4 | Alta |
| **Todas las categorías Objaverse** | ~800.000 | ~8 TB | Meses con GPUs industriales | Media-baja |

Entrenar un modelo de *shape completion* sobre todas las categorías es lo que publican grupos de investigación con infraestructura de cientos de GPUs. En el contexto de un TFM de 14 semanas sobre Colab, es inabordable.

### Por qué la especialización da MEJOR resultado

El modelo de la etapa 3 aprende un "sentido común de la forma" de los objetos que ve. Si solo ve vasijas, cuando falta un asa propone un asa coherente con las demás vasijas que ha visto. Si ha visto de todo (sillas, coches, aviones...), ese sentido común se diluye y la calidad baja en todas las categorías.

> **Veredicto:** una sola categoría (o super-categoría coherente como vasijas) da más calidad, es defendible con datos sólidos, y es la estrategia correcta para un TFM de estas características. "Más categorías" es extensión P1, no objetivo P0.

---

## FAQ 6 — ¿Cómo conseguir el dataset de una categoría lo más grande posible?

La respuesta es **no ampliar a todas las categorías, sino ampliar a una super-categoría semánticamente coherente**.

### La super-categoría "vasijas/recipientes" (cup + mug + bowl + vase)

Estas cuatro categorías tienen la misma topología (objeto hueco, boca abierta, sin partes móviles) y son las más relevantes para el caso de uso del TFM ("se me rompió una pieza de cerámica"). Son la forma de maximizar el dataset sin perder coherencia.

**Cuántos modelos se obtienen por fuente:**

| Fuente | cup | mug | bowl | vase | Total | Uso en el TFM |
|--------|-----|-----|------|------|-------|---------------|
| Objaverse (ya descargado parcialmente) | 70 | 126 | ~200 | ~300 | **~700** | E2 training (renders), E3 training (rotura sintética) |
| CO3D (fotos reales) | ✅ ~450 seq | — | ✅ ~420 seq | ✅ ~360 seq | ~1.230 secuencias | E1 validación, E2 validación/training P1 |
| ShapeNet (acceso pendiente) | ✅ | 214 | 343 | ✅ | ~600+ | E3 training extra (modelos watertight, ideales para rotura sintética) |
| Fantastic Breaks (objetos rotos reales) | cerámica | cerámica | cerámica | cerámica | subconjunto | E3 validación con roturas reales |
| ModelNet40 | 99 | — | 64 | — | 163 | E3 training: todos son watertight, ideales para pares (roto, completo) |

**Total alcanzable sin ShapeNet:** ~700 modelos 3D de Objaverse + 163 de ModelNet40 = **~860 modelos** frente a los ~246 de solo tazas.

### Cómo ampliar el script de descarga de Objaverse

Para descargar también `bowl` y `vase` de Objaverse, edita `Scripts/descargar_tazas.py` y añade las categorías a la lista:

```python
# En descargar_tazas.py, busca la línea con las categorías y añade bowl y vase:
CATEGORIAS = ["mug", "cup", "Dixie_cup", "teacup", "measuring_cup", "bowl", "vase", "pitcher"]
```

El script ya sabe deduplicar si un modelo aparece en varias categorías (por el UID único de Objaverse).

### ModelNet40 — dataset extra para la etapa 3

ModelNet40 es especialmente valioso para la **etapa 3** porque todos sus modelos son **ya watertight** (hechos para benchmarks de ML). Esto significa que los pares (roto, completo) que se generan a partir de ellos son perfectos: sabes exactamente cómo era el objeto entero.

```python
# Descarga ModelNet40 (cup + bowl, 163 modelos watertight)
import urllib.request, zipfile, pathlib

URL = "http://modelnet.cs.princeton.edu/ModelNet40.zip"
DESTINO = pathlib.Path(r"C:\EDF\TFM\Datos\modelnet40")
DESTINO.mkdir(parents=True, exist_ok=True)

print("Descargando ModelNet40 (~435 MB)...")
urllib.request.urlretrieve(URL, DESTINO / "ModelNet40.zip")
with zipfile.ZipFile(DESTINO / "ModelNet40.zip", "r") as z:
    for cat in ["cup", "bowl"]:
        z.extractall(DESTINO, members=[m for m in z.namelist() if m.startswith(f"ModelNet40/{cat}/")])
print("Hecho. Modelos en:", DESTINO / "ModelNet40")
```

> **Recomendación de acción:** (1) Ampliar la descarga de Objaverse a `bowl` y `vase`. (2) Descargar CO3D con `Scripts/descargar_co3d.py` (cup + bowl + vase). (3) Descargar ModelNet40 cup + bowl para tener modelos watertight para la etapa 3. Con esto el dataset pasa de ~246 a ~860+ modelos sin salir de la categoría "vasijas".

---

*(Las próximas dudas se irán añadiendo aquí como FAQ 7, FAQ 8, ...)*
