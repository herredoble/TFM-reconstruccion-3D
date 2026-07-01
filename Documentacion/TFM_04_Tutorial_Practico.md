# Tutorial práctico con código — primeros pasos del TFM

> Guía "manos a la obra" para empezar a tocar código sin miedo.
> Todo lo de las Partes 1-2 se ejecuta **en Google Colab, gratis y sin GPU**.
> Acompaña a la *Guía completa*; aquí se hace, allí se explica el porqué.
> Raquel Roca · Junio 2026

![Diagrama del pipeline del proyecto](C:/edf/tfm/Documentacion/TFM_Diagrama_Pipeline.png)

---

## Parte 0 — Preparar el entorno (5 minutos)

No necesitas instalar nada en tu ordenador para empezar: usaremos **Google Colab**, que es un cuaderno de Python que corre en la nube.

1. Entra en `https://colab.research.google.com` con tu cuenta de Google.
2. Crea un cuaderno nuevo (*Archivo → Nuevo cuaderno*).
3. Un cuaderno tiene **celdas**: escribes código en una y pulsas ▶ (o `Shift+Enter`) para ejecutarla.
4. La primera celda instala las librerías 3D que usaremos:

```python
# Instalar librerías 3D (se ejecuta una vez por sesión de Colab)
!pip install open3d trimesh numpy
print("Librerías instaladas correctamente")
```

> **`!pip install`**: el `!` le dice a Colab que esto es un comando de sistema, no Python. `pip` es el instalador de librerías de Python.

---

## Parte 1 — Conceptos 3D tocándolos: de nube de puntos a STL

Aquí vas a recorrer, en pequeñito, **lo que hace la etapa 4** del proyecto (y a entender de paso qué son una malla y una nube de puntos). Objetivo: cargar un objeto 3D, convertirlo en nube de puntos, reconstruir su superficie y exportarlo como STL imprimible.

### 1.1 Cargar un objeto 3D de ejemplo

Open3D trae modelos de prueba. Usaremos el clásico "conejo de Stanford".

```python
import open3d as o3d
import numpy as np

# Open3D incluye modelos de ejemplo; descargamos el conejo de Stanford
bunny = o3d.data.BunnyMesh()
mesh = o3d.io.read_triangle_mesh(bunny.path)
mesh.compute_vertex_normals()   # calcular normales para que se vea bien

# Información básica del objeto
print("¿Cuántos vértices (puntos) tiene?:", len(mesh.vertices))
print("¿Cuántas caras (triángulos) tiene?:", len(mesh.triangles))
```

> Lo que acabas de cargar es una **malla**: vértices unidos en triángulos. Los números que imprime son, literalmente, cuántos puntos y cuántos triángulos forman el conejo.

### 1.2 Convertir la malla en una nube de puntos

Así simulamos lo que daría un escáner o la fotogrametría: puntos sueltos sobre la superficie.

```python
# Muestrear 3000 puntos repartidos por la superficie del conejo
pcd = mesh.sample_points_poisson_disk(number_of_points=3000)
print("Puntos en la nube:", len(pcd.points))

# Guardar la nube en un archivo (formato .ply)
o3d.io.write_point_cloud("conejo_nube.ply", pcd)
print("Nube de puntos guardada en conejo_nube.ply")
```

> Una **nube de puntos** no se puede imprimir: son puntos sin superficie entre ellos. El siguiente paso es "ponerle piel".

### 1.3 Reconstruir la superficie (nube → malla)

Usamos **reconstrucción de Poisson**, que crea una superficie cerrada a partir de la nube. Necesita que cada punto tenga una **normal** (la dirección hacia "fuera").

```python
# 1) Estimar las normales de cada punto (hacia dónde mira la superficie)
pcd.estimate_normals()

# 2) Reconstrucción de Poisson: nube de puntos -> malla cerrada
mesh_rec, densidades = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    pcd, depth=8
)
print("Malla reconstruida con", len(mesh_rec.triangles), "triángulos")
```

> **`depth=8`** controla el nivel de detalle: más alto = más detalle pero más lento y más triángulos. Es un "parámetro" típico con el que experimentarás.

### 1.4 Comprobar si es imprimible (watertight) y repararla

```python
import trimesh

# Pasar la malla de Open3D a Trimesh (que sabe comprobar imprimibilidad)
vertices = np.asarray(mesh_rec.vertices)
caras    = np.asarray(mesh_rec.triangles)
tm = trimesh.Trimesh(vertices=vertices, faces=caras)

print("¿Es watertight (cerrada/imprimible)?:", tm.is_watertight)

# Reparaciones típicas: arreglar normales y rellenar agujeros
tm.fix_normals()
trimesh.repair.fill_holes(tm)
print("Tras reparar, ¿es watertight?:", tm.is_watertight)
```

> `is_watertight` responde sí/no a la pregunta clave de la etapa 4: ¿está la malla completamente cerrada? Si no, no se puede imprimir.

### 1.5 Exportar a STL (¡el archivo final del proyecto!)

```python
# Exportar a STL, el formato que entiende una impresora 3D
tm.export("conejo_final.stl")
print("¡Listo! Archivo STL generado: conejo_final.stl")

# En Colab, descargarlo a tu ordenador:
from google.colab import files
files.download("conejo_final.stl")
```

> Acabas de recorrer, en miniatura, el final del pipeline: **nube de puntos → malla → reparación → STL**. Este STL lo podrías abrir en un *laminador* (Cura/PrusaSlicer) e imprimir.

### 1.6 Ver el resultado (visualización en Colab)

Colab no abre la ventana 3D interactiva de Open3D, pero podemos pintar la nube con una librería de gráficos:

```python
import matplotlib.pyplot as plt

puntos = np.asarray(pcd.points)
fig = plt.figure(figsize=(5,5))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(puntos[:,0], puntos[:,1], puntos[:,2], s=1)
ax.set_title("Nube de puntos del conejo")
plt.show()
```

> En tu ordenador (no en Colab), `o3d.visualization.draw_geometries([mesh])` abriría un visor 3D donde girar el objeto con el ratón. Para verlo bonito, **Blender** o **MeshLab** son ideales.

---

## Parte 2 — Entender la etapa 3: "romper" un objeto para luego repararlo

La etapa 3 (reparación) se entrena con pares **(objeto roto → objeto completo)**. Aquí ves cómo se **fabrica** un objeto "roto" a partir de uno completo: justo el dato que necesita la IA para aprender.

```python
import open3d as o3d
import numpy as np

# Partimos de la nube completa del conejo (Parte 1)
pcd = o3d.io.read_point_cloud("conejo_nube.ply")
puntos = np.asarray(pcd.points)

# "Romper" el objeto: eliminar todos los puntos por encima de cierta altura (eje Y)
umbral_y = np.median(puntos[:,1])         # altura media del conejo
mascara = puntos[:,1] < umbral_y          # nos quedamos solo con la mitad de abajo
puntos_rotos = puntos[mascara]

print("Puntos originales:", len(puntos))
print("Puntos tras 'romper':", len(puntos_rotos))

# Guardar el objeto "roto" como nuevo ejemplo
pcd_roto = o3d.geometry.PointCloud()
pcd_roto.points = o3d.utility.Vector3dVector(puntos_rotos)
o3d.io.write_point_cloud("conejo_roto.ply", pcd_roto)
print("Objeto 'roto' guardado: la IA aprendería a reconstruir la parte que quitamos")
```

> Esto se llama **generar datos sintéticos de rotura** (un tipo de *data augmentation*). Con un dataset de objetos completos puedes crear miles de pares (roto → completo) sin necesitar objetos rotos reales. Combinado con el dataset **Fantastic Breaks** (roturas reales), tendrías material de sobra para entrenar la etapa 3.

---

## Parte 3 — De fotos reales a 3D: la etapa 2 con herramientas

Esto ya no corre cómodamente en Colab (necesita GPU y, a veces, instalar programas), pero conviene que entiendas **los comandos y el flujo**. Dos caminos:

### Camino A — Fotogrametría con COLMAP (sin deep learning)
COLMAP es un programa con interfaz. El flujo, conceptualmente, es:
1. Metes ~30-50 fotos del objeto en una carpeta.
2. *Feature extraction*: COLMAP busca puntos característicos en cada foto.
3. *Feature matching*: empareja esos puntos entre fotos.
4. *Sparse reconstruction (SfM)*: deduce las **poses de cámara** y una nube de puntos rala.
5. *Dense reconstruction (MVS)*: densifica → nube de puntos detallada → malla.

### Camino B — Gaussian Splatting / NeRF con Nerfstudio (con deep learning)
**Nerfstudio** es una herramienta que facilita entrenar NeRF y Gaussian Splatting. Flujo típico (en una máquina con GPU, p. ej. Colab Pro):

```bash
# Instalar nerfstudio (en un entorno con GPU)
pip install nerfstudio

# 1) Procesar tus fotos o vídeo: extrae fotogramas y calcula poses (usa COLMAP por dentro)
ns-process-data images --data MIS_FOTOS/ --output-dir datos_procesados/

# 2) Entrenar un modelo (aquí, Gaussian Splatting)
ns-train splatfacto --data datos_procesados/

# 3) Exportar la geometría a malla / nube de puntos
ns-export poisson --load-config CONFIG.yml --output-dir salida/
```

> No te aprendas los comandos de memoria: lo importante es ver que es **"procesar fotos → entrenar → exportar malla"**. Esa malla exportada es justo la entrada de tu etapa 3.

---

## Parte 4 — Cómo es por dentro "entrenar una red" (PyTorch)

Para que el concepto de "entrenar" deje de ser abstracto, este es el **esqueleto universal** de un entrenamiento en PyTorch. Casi todo entrenamiento, por complejo que sea, tiene esta forma:

```python
import torch

# 1) EL MODELO: la red con sus "perillas" (pesos) ajustables.
#    Aquí una red minúscula de ejemplo; la real sería mucho mayor.
modelo = torch.nn.Sequential(
    torch.nn.Linear(10, 64),   # capa: de 10 números de entrada a 64
    torch.nn.ReLU(),           # "activación" (no linealidad)
    torch.nn.Linear(64, 3),    # capa: de 64 a 3 números de salida
)

# 2) LA PÉRDIDA: cómo medimos el error entre la predicción y la respuesta correcta.
funcion_perdida = torch.nn.MSELoss()

# 3) EL OPTIMIZADOR: el que ajusta las perillas para equivocarse menos.
optimizador = torch.optim.Adam(modelo.parameters(), lr=0.001)

# 4) EL BUCLE DE ENTRENAMIENTO: se repite muchas veces ("épocas").
for epoca in range(100):
    for entrada, respuesta_correcta in cargador_de_datos:   # recorre el dataset
        prediccion = modelo(entrada)                        # la red "adivina"
        error = funcion_perdida(prediccion, respuesta_correcta)  # ¿cuánto falla?

        optimizador.zero_grad()   # poner a cero los ajustes previos
        error.backward()          # calcular cómo mover cada perilla (gradiente)
        optimizador.step()        # mover las perillas un poquito

    print(f"Época {epoca}: error = {error.item():.4f}")   # debería ir bajando
```

> En tu etapa: la **entrada** serían fotos o una nube parcial, la **respuesta correcta** sería el objeto 3D real, y la **pérdida** mediría la diferencia entre formas (p. ej. con *Chamfer distance*). El esqueleto es siempre el mismo: **predecir → medir error → ajustar → repetir**.

---

## Parte 5 — Envolverlo en una app (etapa 5) con Gradio

Con muy poco código, Gradio crea una web donde subir fotos y descargar el STL. Este es el esqueleto:

```python
import gradio as gr

def reconstruir_objeto(lista_de_fotos):
    # Aquí dentro irían, encadenadas, tus etapas 1->4:
    #   1. preprocesar las fotos
    #   2. reconstruir el 3D
    #   3. reparar
    #   4. exportar a STL
    ruta_stl = "conejo_final.stl"   # (de momento devolvemos uno de ejemplo)
    return ruta_stl

demo = gr.Interface(
    fn=reconstruir_objeto,
    inputs=gr.File(file_count="multiple", label="Sube tus fotos"),
    outputs=gr.File(label="Descarga tu modelo STL"),
    title="Reconstrucción 3D a partir de fotos",
    description="Sube varias fotos de un objeto y obtén un STL listo para imprimir."
)

demo.launch()   # abre una web local con la interfaz
```

> Esto te da, casi gratis, la "cara visible" del TFM. Se puede publicar en **Hugging Face Spaces** para enseñarlo con un simple enlace.

---

## Qué hacer esta semana (mini plan de arranque)

1. Abre Colab y ejecuta entera la **Parte 1**: termina con un STL descargado. Es tu primer "de cero a objeto imprimible".
2. Haz la **Parte 2** ("romper" el conejo): entenderás los datos de la etapa 3.
3. Instala **MeshLab** (gratis) en tu ordenador y abre ahí el `conejo_final.stl` para verlo y girarlo.
4. Mira un tutorial introductorio de **PyTorch** (el oficial "60 minute blitz") para afianzar la Parte 4.
5. Cuando el grupo reparta etapas, busca **un repositorio público** de tu método (NeRF/Gaussian Splatting si te toca la 2; PoinTr u otro de *shape completion* si la 3) y **reprodúcelo** antes de tocar nada. Reproducir primero, innovar después.

> **Recuerda la regla de oro del proyecto:** primero que funcione el **núcleo P0** de punta a punta sobre una categoría de objetos; las mejoras vienen después.
