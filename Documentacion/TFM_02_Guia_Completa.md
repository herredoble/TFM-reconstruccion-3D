# Guía completa del TFM — Reconstrucción 3D y reimpresión de objetos a partir de fotos

> Manual desde cero: conceptos, herramientas y proceso paso a paso.
> Pensado para entenderlo sin conocimientos previos de 3D ni de inteligencia artificial.
> Raquel Roca · Junio 2026

---

## 0. Cómo leer esta guía

Esta guía está pensada para llevarte de "no tengo ni idea" a "entiendo qué hay que hacer y por qué". El orden recomendado:

1. Primero los **conceptos base** (secciones 1 y 2): el vocabulario. Sin esto, lo demás no se entiende.
2. Luego la **visión global** (sección 3): el mapa del proyecto entero.
3. Después las **herramientas** (sección 4): qué programas existen y para qué sirve cada uno.
4. Y por fin el **proceso etapa por etapa** (secciones 5 a 9), que es el corazón.
5. Al final: **evaluación**, **entorno de trabajo**, **plan de aprendizaje** y un **glosario** para consultar.

No hace falta memorizar nada. Lee de corrido la primera vez y vuelve a las secciones concretas cuando trabajes en ellas.

---

## 1. Conceptos base: ¿qué es "3D" para un ordenador?

Cuando hablamos de un "modelo 3D" dentro de un ordenador, no es una foto ni un vídeo: es una **descripción matemática de la forma de un objeto en el espacio**. Hay varias maneras de guardar esa forma, y entenderlas es la clave de todo el proyecto.

### 1.1 El espacio 3D y las coordenadas (X, Y, Z)
Todo punto en el espacio se describe con tres números: **X** (izquierda-derecha), **Y** (arriba-abajo) y **Z** (delante-detrás). Igual que en un mapa usas latitud y longitud (2 números), en 3D usas 3. Un objeto 3D es, en el fondo, un montón de puntos colocados en esas coordenadas.

### 1.2 Nube de puntos (point cloud)
Es la forma más simple de representar un objeto: **una lista de puntos sueltos en el espacio**, cada uno con sus coordenadas (X, Y, Z) y a veces su color. Imagina que pulverizas el contorno de un objeto con miles de motitas: eso es una nube de puntos. Es lo que produce un escáner láser o la fotogrametría.

- **Ventaja:** fácil de generar y de manejar.
- **Inconveniente:** son puntos sueltos, no una superficie continua. No puedes imprimir una nube de puntos: tiene "agujeros" entre punto y punto.

### 1.3 Malla (mesh) — lo más importante
Una **malla** es la representación estrella en 3D. Se construye uniendo puntos (llamados **vértices**) con líneas (**aristas**) para formar pequeños **triángulos** (**caras**). Miles de triángulos pegados forman la "piel" o superficie del objeto, como una red de pescador que envuelve la forma.

- Casi todos los objetos 3D que ves en videojuegos, películas o impresión 3D **son mallas de triángulos**.
- El formato **STL** (el que necesita la impresora 3D) es precisamente una malla de triángulos.

### 1.4 Vóxel (voxel)
Un vóxel es como un **píxel pero en 3D**: un cubito. Representar un objeto con vóxeles es como construirlo con piezas de LEGO o Minecraft: llenas de cubitos el volumen que ocupa el objeto. Es intuitivo pero "pesa" mucho y se ve cuadriculado si los cubos son grandes.

### 1.5 Funciones implícitas (SDF y campos de ocupación)
Esta es más abstracta pero **fundamental en la IA moderna de 3D**. En vez de guardar puntos o triángulos, guardas una **función matemática** que, para cualquier punto del espacio, te dice algo sobre él:

- **Campo de ocupación (occupancy):** la función responde "¿este punto está DENTRO o FUERA del objeto?" (sí/no).
- **SDF (Signed Distance Function, función de distancia con signo):** la función responde "¿a qué distancia estoy de la superficie del objeto, y estoy dentro (negativo) o fuera (positivo)?".

¿Por qué mola? Porque una red neuronal puede **aprender** esa función. En lugar de almacenar millones de triángulos, almacenas una red que "sabe" la forma. Luego, cuando quieres la malla, le preguntas a la función en muchos puntos y reconstruyes la superficie (con un algoritmo llamado **Marching Cubes**, ver sección 8).

### 1.6 Textura
La **textura** es el "color y aspecto de la superficie": la imagen que se pega sobre la malla para que parezca madera, metal, piel, etc. Para imprimir en 3D **la textura no importa** (la impresora solo necesita la forma), así que en este proyecto es secundaria. Nos centramos en la **geometría** (la forma).

### 1.7 "Watertight" (estanco) y por qué importa para imprimir
Una malla es **watertight** ("estanca", literalmente "que no deja pasar agua") cuando está **completamente cerrada, sin agujeros ni bordes sueltos**: define claramente un dentro y un fuera, como una botella cerrada.

- Para **imprimir en 3D, la malla DEBE ser watertight.** Si tiene agujeros, la impresora no sabe qué es macizo y qué es hueco, y falla.
- Gran parte del trabajo de la etapa 4 es convertir una malla con defectos en una watertight.

### 1.8 El formato STL
**STL** es el formato de archivo estándar para impresión 3D. Guarda únicamente la **malla de triángulos** (la forma), sin color. Es el "documento final" que tu proyecto debe producir y que se envía a la impresora (a través de un programa "laminador", ver glosario).

---

## 2. Conceptos base: ¿qué es la inteligencia artificial que vamos a usar?

El proyecto usa **deep learning** (aprendizaje profundo). Aquí van las ideas mínimas para entenderlo.

### 2.1 Red neuronal, en una frase
Una **red neuronal** es una función matemática enorme con millones de "perillas" ajustables (llamadas **parámetros** o **pesos**). Le entras datos (p. ej. una imagen) y te saca un resultado (p. ej. una forma 3D). Por sí sola no sabe nada: hay que **entrenarla**.

### 2.2 Entrenar (training)
Entrenar es el proceso de **ajustar esas millones de perillas** para que la red haga bien su tarea. Se hace así:
1. Le enseñas un ejemplo del que conoces la respuesta correcta (p. ej. fotos de una silla + su modelo 3D real).
2. La red da su respuesta (al principio, fatal).
3. Mides **cuánto se equivoca** con una "función de pérdida" (loss).
4. Un algoritmo (**descenso de gradiente**) ajusta un poquito las perillas para equivocarse menos.
5. Repites esto millones de veces con miles de ejemplos.

Al final, la red "ha aprendido" y funciona también con ejemplos nuevos que nunca vio.

### 2.3 Dataset (conjunto de datos)
El **dataset** es la colección de ejemplos con los que entrenas. En nuestro caso, datasets de objetos 3D (ShapeNet, Objaverse...) o de objetos rotos↔completos (Fantastic Breaks). **Sin un buen dataset no hay deep learning**: es la materia prima.

- **Entrenamiento / validación / test:** el dataset se parte en tres. Con el de **entrenamiento** la red aprende; con el de **validación** vas comprobando que mejora; y el de **test** se guarda hasta el final para medir, con ejemplos que la red nunca vio, cómo de bien funciona de verdad.

### 2.4 GPU (tarjeta gráfica) y por qué hace falta
Entrenar redes requiere hacer muchísimos cálculos en paralelo. Las **GPU** (las tarjetas gráficas, p. ej. de NVIDIA) son hardware especializado en eso. Entrenar en una CPU normal puede tardar semanas; en GPU, horas. **No tendréis que comprar una:** se usan GPUs gratuitas/baratas en la nube (Google Colab, Kaggle), ver sección 11.

### 2.5 Modelo preentrenado y "fine-tuning"
Muchas veces **no entrenas desde cero**. Partes de un **modelo preentrenado** (una red que alguien ya entrenó con millones de ejemplos y publicó) y solo lo **ajustas un poco** a tu caso concreto (**fine-tuning**). Esto ahorra muchísimo tiempo y datos, y es lo que probablemente haréis.

### 2.6 Modelo generativo
Un **modelo generativo** es una red que **crea cosas nuevas** en lugar de solo clasificar. Los que generan imágenes a partir de texto (tipo "dame un gato astronauta") son generativos. En nuestro proyecto, la etapa 3 (reparar la parte que falta de un objeto) es generativa: la red **inventa de forma plausible** el trozo ausente. Familias típicas: **autoencoders**, **GANs**, **modelos de difusión** (diffusion), **transformers**.

---

## 3. Visión global: el pipeline del proyecto

"**Pipeline**" significa "tubería": una cadena de etapas donde la salida de una es la entrada de la siguiente. El nuestro convierte **fotos** en un **objeto imprimible**:

**Fotos → [1] Preprocesado → [2] Reconstrucción 3D → [3] Reparación → [4] Exportar STL → [5] App**

Una analogía: es como **restaurar un jarrón roto a partir de fotos**:
- Etapa 1: limpias y ordenas las fotos (quitas el fondo, sabes desde dónde se tomó cada una).
- Etapa 2: a partir de las fotos, reconstruyes la forma del jarrón en 3D.
- Etapa 3: si le falta un trozo, lo "inventas" de forma coherente con el resto.
- Etapa 4: preparas la pieza para que se pueda fabricar (cerrada, sólida).
- Etapa 5: pones todo en una aplicación donde alguien sube fotos y recibe el archivo.

Recuerda la **estrategia del proyecto** (decidida en la propuesta): el corazón son las **etapas 2 y 3** (las de IA); las etapas 1, 4 y 5 se resuelven en gran parte con **herramientas que ya existen**.

---

## 4. Las herramientas: ¿con qué programas se hace esto?

Aquí está el "taller" completo. No hay que dominar todo desde el día 1; esta lista es tu mapa.

### 4.1 El lenguaje: Python
Casi todo en IA se programa en **Python**, un lenguaje sencillo de leer. Será vuestro idioma principal. Las "recetas" de código se suelen escribir en **notebooks** (ver Jupyter/Colab abajo).

### 4.2 Librerías de deep learning: PyTorch
Una **librería** es un conjunto de herramientas de código ya hechas que importas en tu programa. **PyTorch** (de Meta) es la librería estándar para construir y entrenar redes neuronales; es la que usa casi toda la investigación de 3D. (Alternativa: TensorFlow, pero para este proyecto PyTorch es lo habitual.)

### 4.3 Librerías para manejar 3D
- **Open3D:** la navaja suiza para nubes de puntos y mallas en Python (cargar, visualizar, limpiar, reconstruir superficies, exportar STL). La usaréis mucho, sobre todo en etapas 1 y 4.
- **Trimesh:** otra librería de Python muy práctica para cargar/editar mallas y comprobar si son watertight.
- **PyTorch3D** (de Meta) / **Kaolin** (de NVIDIA): librerías que conectan el 3D con el deep learning (cálculos de mallas/nubes dentro de redes). Útiles en etapas 2 y 3.

### 4.4 Programas de modelado/edición 3D (con interfaz visual)
- **Blender:** programa gratuito y potentísimo para crear y editar 3D. Lo usaréis sobre todo para **visualizar** resultados, preparar datos y hacer figuras bonitas para la memoria. Tiene también consola Python.
- **MeshLab:** programa gratuito especializado en **procesar y reparar mallas** (cerrar agujeros, simplificar, limpiar). Muy útil en la etapa 4.
- **MeshLab/Blender** son para "ver y tocar con el ratón"; **Open3D/Trimesh** son para "hacer lo mismo desde código, de forma automática".

### 4.5 Fotogrametría: COLMAP
**COLMAP** es un programa gratuito que, dadas varias fotos de un objeto, **calcula desde dónde se tomó cada foto** (la "pose" de la cámara) y reconstruye una nube de puntos. Es el estándar para la parte de "fotos reales → 3D" y lo usaréis como herramienta en las etapas 1 y 2.

### 4.6 Segmentación de imágenes: SAM
**SAM (Segment Anything Model, de Meta)** es una red ya entrenada que **separa el objeto del fondo** en una foto con muy poco esfuerzo. Lo usaréis en la etapa 1 para quedaros solo con el objeto.

### 4.7 Métodos de reconstrucción modernos
- **NeRF (Neural Radiance Fields):** técnica que aprende una escena 3D a partir de fotos para poder generar vistas nuevas; sirve para reconstruir forma. (Implementación práctica popular: **Nerfstudio**, **Instant-NGP**.)
- **Gaussian Splatting (3DGS):** técnica más reciente y rápida que representa la escena con "manchas" gaussianas; muy de moda para reconstrucción a partir de fotos.
- **Métodos image-to-3D** (p. ej. modelos tipo **LRM**, **Zero-1-to-3**): redes que generan un objeto 3D directamente desde una o pocas imágenes.

### 4.8 Para la app (etapa 5)
- **Gradio** o **Streamlit:** librerías de Python que crean una **interfaz web sencilla** (subir fotos, ver resultado, descargar archivo) con muy poco código. Ideales para una demo de TFM sin ser expertos en desarrollo web.

### 4.9 Para organizarse y entrenar
- **Git y GitHub:** para guardar el código, llevar versiones y trabajar los 5 sin pisaros (ver sección 11).
- **Jupyter Notebook / Google Colab:** entornos donde escribes y ejecutas Python por trozos, mezclando código, texto y resultados. **Colab** además te da **GPU gratis** en la nube.
- **Conda / venv:** herramientas para crear "entornos" aislados con las versiones correctas de cada librería (evita el clásico "en mi ordenador funcionaba").
- **Weights & Biases / TensorBoard:** paneles para ver gráficas del entrenamiento (cómo baja el error con el tiempo).

---

## 5. Etapa 1 — Captura y preprocesado de imágenes

**Objetivo:** conseguir un conjunto de fotos "limpias" del objeto y saber desde dónde se tomó cada una, para que la etapa 2 pueda reconstruir bien.

### 5.1 Conceptos
- **Multivista (multi-view):** varias fotos del mismo objeto desde **ángulos distintos**. Cuantos más ángulos, mejor se reconstruye (como dar vueltas alrededor para verlo entero).
- **Segmentación:** separar en la imagen qué píxeles son el **objeto** y cuáles el **fondo**, para quedarte solo con el objeto.
- **Pose de la cámara:** la posición y orientación desde la que se tomó cada foto (dónde estaba la cámara y hacia dónde miraba). Es **imprescindible** para cruzar la información de varias fotos.
- **Structure-from-Motion (SfM):** técnica (la que usa COLMAP) que, comparando puntos comunes entre fotos, deduce a la vez las poses de las cámaras y una nube de puntos inicial. "Structure from motion" = "estructura a partir del movimiento (de la cámara)".

### 5.2 Qué harías, paso a paso
1. **Conseguir imágenes.** En el MVP, lo más cómodo es **renderizar fotos sintéticas** desde modelos 3D de un dataset (p. ej. ShapeNet): coges un modelo, lo "fotografías" virtualmente desde 30-50 ángulos con Blender. Ventaja: ya conoces la pose exacta y la forma real (ground truth). Más adelante (P1) podéis usar fotos reales (CO3D) o hechas por vosotros.
2. **Segmentar** cada imagen con **SAM** para quitar el fondo.
3. **Estimar poses** con **COLMAP** (si usáis fotos reales) o usarlas directamente (si son sintéticas, ya las tenéis).
4. **Normalizar:** ajustar tamaño, centrar el objeto, igualar iluminación. Dejar todo en un formato estándar.

**Salida de la etapa:** un paquete ordenado de imágenes + sus poses, listo para la etapa 2.

---

## 6. Etapa 2 — Reconstrucción 3D (núcleo del TFM)

**Objetivo:** convertir las imágenes (+ poses) en una **representación 3D** del objeto (nube de puntos o malla).

### 6.1 Las dos grandes familias de métodos
**A) Fotogrametría clásica (sin deep learning).** A partir de las fotos y poses, se reconstruye la geometría buscando correspondencias geométricas. Herramientas: COLMAP (+ MVS, *Multi-View Stereo*). Es robusta y no necesita entrenar, pero falla con superficies brillantes, transparentes o sin textura.

**B) Métodos con deep learning (lo interesante para el TFM).**
- **NeRF:** una red aprende una función que, dado un punto del espacio y una dirección de mirada, dice qué color y densidad hay ahí. Entrenándola con vuestras fotos, "memoriza" la escena en 3D y permite extraer la forma. Intuición: la red rellena el volumen entre las fotos.
- **Gaussian Splatting:** en vez de una red densa, representa la escena con millones de "manchas" 3D semitransparentes (gaussianas) que se optimizan para reproducir las fotos. Es **más rápido** que NeRF y da muy buena calidad. Muy recomendable como método moderno.
- **Image-to-3D directo (p. ej. LRM):** redes ya entrenadas que, dada una o pocas imágenes, **predicen directamente** una representación 3D (malla, nube o SDF). Aquí entra el **fine-tuning**: partir de un modelo publicado y adaptarlo a vuestra categoría de objetos.

### 6.2 Qué harías, paso a paso
1. **Elegir un método** (recomendado para aprender: empezar por Gaussian Splatting con una herramienta lista como Nerfstudio; en paralelo, explorar un método image-to-3D para el componente de "aprendizaje" del TFM).
2. **Preparar los datos** que salieron de la etapa 1.
3. **Entrenar/optimizar** el modelo para vuestro objeto o categoría (aquí entra la GPU).
4. **Extraer la geometría:** convertir lo aprendido en una **malla** o **nube de puntos** (de NeRF/SDF se saca malla con Marching Cubes; de Gaussian Splatting hay métodos específicos).
5. **Comparar métodos** y medir calidad con métricas (sección 10). Comparar es justo lo que da contenido de TFM.

**Salida de la etapa:** una malla/nube 3D del objeto reconstruido (posiblemente **incompleta o con defectos** — eso lo arregla la etapa 3).

---

## 7. Etapa 3 — Reparación y completado (núcleo del TFM, lo más original)

**Objetivo:** dado un objeto 3D **incompleto o roto**, **rellenar de forma realista la parte que falta**.

### 7.1 Conceptos
- **Shape completion (completado de forma):** tarea de IA que toma una forma parcial y predice la forma completa. Ejemplo clásico: te dan media silla y la red completa la otra mitad de forma coherente.
- **Inpainting 3D:** "inpainting" es rellenar huecos; en imágenes 2D es borrar un objeto y que la IA reconstruya el fondo. En 3D es lo mismo pero con volumen.
- **Aprendizaje supervisado con pares:** se entrena mostrando a la red **pares (roto → completo)**. La red aprende a predecir el completo a partir del roto. El dataset **Fantastic Breaks** es exactamente esto (objetos reales rotos + su versión entera). También se pueden **fabricar** datos rotos artificialmente: coges objetos completos y les borras trozos a propósito (data augmentation), así generas pares infinitos.

### 7.2 Cómo funciona la red (intuición)
La red aprende una especie de "sentido común de las formas": tras ver miles de jarrones, sabe cómo es un jarrón típico, así que si le falta un asa, **propone un asa plausible**. Técnicamente suele trabajar sobre una representación que la IA maneja bien: **nube de puntos**, **vóxeles** o, lo más moderno, una **función implícita (SDF/ocupación)** dentro de un modelo generativo (autoencoder, transformer tipo PoinTr, o difusión).

### 7.3 Qué harías, paso a paso
1. **Elegir representación y modelo** (p. ej. completado de nube de puntos con un modelo tipo PoinTr, o un enfoque basado en SDF).
2. **Preparar los pares (parcial → completo):** con Fantastic Breaks y/o generando roturas artificiales sobre objetos completos.
3. **Entrenar** la red con esos pares (GPU).
4. **Aplicarla** a la salida de la etapa 2 (el objeto reconstruido e incompleto) para obtener la versión completa.
5. **Evaluar** cuánto se parece lo reparado a la realidad (métricas, sección 10).

**Salida de la etapa:** un objeto 3D **completo**, listo para convertir en STL.

---

## 8. Etapa 4 — Generación del STL imprimible

**Objetivo:** convertir la forma reparada en un **archivo STL válido y físicamente imprimible**.

### 8.1 Conceptos
- **Mallado (meshing):** convertir una nube de puntos o una función implícita en una **malla de triángulos**. Algoritmos clave:
  - **Marching Cubes:** recorre el espacio en una rejilla y, allí donde la superficie cruza, coloca triángulos. Es como "envolver" la forma implícita con una piel de triángulos. Es el puente típico entre la IA (SDF/ocupación) y la malla.
  - **Poisson Surface Reconstruction:** reconstruye una superficie suave y cerrada a partir de una nube de puntos. Disponible en Open3D.
- **Reparación de malla (mesh repair):** arreglar defectos para hacerla **watertight**: cerrar agujeros, eliminar caras sueltas, corregir **normales** (la "orientación" de cada triángulo: hacia dónde es el "fuera"), quitar auto-intersecciones.
- **Simplificación / decimation:** reducir el número de triángulos si son demasiados, para que el archivo no pese de más, sin perder forma.
- **Manifold ("variedad"):** una malla bien formada donde cada arista conecta exactamente dos caras (sin geometría "imposible"). Las impresoras necesitan mallas manifold y watertight.

### 8.2 Qué harías, paso a paso (casi todo con herramientas)
1. **Mallar** la salida de la etapa 3 (Marching Cubes o Poisson, con Open3D).
2. **Reparar** la malla (Open3D / Trimesh / MeshLab): cerrar, orientar normales, quitar basura.
3. **Comprobar imprimibilidad:** que sea watertight y manifold (Trimesh lo verifica; herramientas como el "make solid" de MeshLab/Meshmixer ayudan).
4. **Simplificar** si hace falta y **exportar a `.STL`**.
5. (Opcional, P2) Abrir el STL en un **laminador** (Cura, PrusaSlicer) y, si tenéis impresora, **imprimirlo de verdad** — una foto del objeto impreso es oro para la defensa.

**Salida de la etapa:** el archivo `.STL` final.

---

## 9. Etapa 5 — Aplicación end-to-end

**Objetivo:** juntar todo en algo **usable**: alguien sube fotos y recibe el STL.

### 9.1 Qué harías, paso a paso
1. **Encadenar el pipeline** en un único script: entrada = fotos; salida = STL, pasando por las etapas 1→4.
2. **Envolverlo en una interfaz** con **Gradio** o **Streamlit**: una página web sencilla con un botón de "subir fotos", un visor 3D del resultado y un botón de "descargar STL".
3. (Opcional) Desplegarlo en la nube (Hugging Face Spaces es gratis y fácil) para enseñarlo con un enlace.

**Salida de la etapa:** la demo del TFM.

---

## 10. ¿Cómo se sabe si funciona? Evaluación y métricas

En un TFM no basta con "se ve bien": hay que **medir** con números. Estas son las métricas clave (explicadas):

- **Chamfer Distance (distancia de Chamfer):** mide cómo de lejos está, en promedio, cada punto de tu forma reconstruida del punto más cercano de la forma real (y viceversa). **Más bajo = mejor.** Es la métrica reina para comparar formas 3D.
- **IoU (Intersection over Union, en volumen):** mide cuánto se solapa el volumen de tu objeto con el real, dividido por el volumen total que ocupan entre los dos. Va de 0 a 1; **más alto = mejor** (1 = idénticos).
- **F-Score:** combina "precisión" (qué parte de lo que reconstruiste es correcto) y "exhaustividad" (qué parte de lo real lograste reconstruir).
- **Normal consistency:** mide si las superficies "miran" en la misma dirección que las reales (calidad fina de la superficie).
- **Métricas de imprimibilidad (etapa 4):** ¿es watertight? ¿es manifold? ¿cuántos agujeros tenía antes de reparar? Son métricas más de "sí/no" o conteos.

**Idea clave:** para poder medir necesitas un **ground truth** (la forma real). Por eso al principio conviene usar datos sintéticos (sabes la forma exacta) y dividir el dataset en train/validación/test.

---

## 11. El entorno de trabajo (cómo se trabaja en la práctica)

- **Python + un entorno aislado** (Conda o venv) con las librerías fijadas, para que los 5 tengáis lo mismo.
- **GitHub** como repositorio común: cada uno trabaja en su "rama", y se juntan los cambios. Imprescindible siendo 5 personas.
- **Google Colab / Kaggle** para entrenar con **GPU gratis** al principio. Si os quedáis cortos, hay opciones de pago baratas (Colab Pro, runpod, vast.ai) o quizá GPUs de la universidad.
- **Estructura de carpetas clara:** `datos/`, `código por etapa/`, `modelos entrenados/`, `resultados/`, `memoria/`.
- **Las "interfaces" entre etapas** (acordadas la primera semana): por ejemplo, "la etapa 2 entrega siempre una malla en formato `.obj` con tal escala y orientación". Esto permite trabajar en paralelo sin bloquearos.

---

## 12. Plan de aprendizaje sugerido (en qué orden meterse)

Para volverte experta sin agobiarte, un orden razonable:

1. **Python básico** (si no lo tienes muy fresco): variables, funciones, listas, y cómo usar notebooks.
2. **Conceptos de 3D** (sección 1 de esta guía) jugando con **Blender** y **MeshLab**: carga un modelo, gíralo, míralo como malla, exporta un STL. Toca para perder el miedo.
3. **Open3D / Trimesh:** cargar una nube de puntos y una malla desde código, visualizarlas, exportar STL. Es la base de las etapas 1 y 4.
4. **Fundamentos de deep learning con PyTorch:** un tutorial introductorio (entrenar una red simple). Entender bien "entrenar = ajustar pesos con datos".
5. **Tu etapa concreta en profundidad:** según te toque la 2 o la 3, leer 2-3 papers clave (sección de bibliografía de la propuesta) y reproducir un repositorio existente antes de innovar.
6. **Fotogrametría práctica:** seguir un tutorial de **COLMAP** o **Nerfstudio** con fotos propias para entender la etapa 2 de punta a punta.

**Consejo:** primero **reproducir** algo que ya funciona (un repo público), y solo después modificarlo. Aprenderás muchísimo más rápido que empezando de cero.

---

## 13. Errores y dificultades típicas (para anticiparlas)

- **Esperar fotos perfectas:** objetos brillantes, transparentes o sin textura se reconstruyen mal. Elegir una categoría "amable" (mate, con textura).
- **Subestimar la integración:** que cada etapa funcione por separado no garantiza que encajen. Por eso se fijan las interfaces pronto y se reserva agosto.
- **Datasets pesados:** Objaverse-XL son terabytes. Descargar solo un **subconjunto** de la categoría elegida.
- **GPU insuficiente:** algunos métodos piden mucha memoria de GPU. Empezar con objetos pequeños/baja resolución.
- **Mallas no imprimibles:** casi siempre hay que reparar antes de exportar. No dar por hecho que la malla sale watertight.
- **Querer abarcar demasiado:** mantener el alcance del **núcleo P0** y dejar lo demás como extensión.

---

## 14. Glosario rápido

- **Vértice / arista / cara:** punto / línea / triángulo que forman una malla.
- **Malla (mesh):** superficie de triángulos que describe la forma.
- **Nube de puntos:** conjunto de puntos sueltos con coordenadas.
- **Vóxel:** cubito; píxel en 3D.
- **SDF / ocupación:** funciones que describen una forma (distancia a la superficie / dentro-fuera).
- **Watertight:** malla cerrada, sin agujeros; imprimible.
- **Manifold:** malla bien formada (cada arista, dos caras).
- **STL:** formato de archivo de malla para impresión 3D.
- **Pose de cámara:** posición y orientación desde la que se toma una foto.
- **SfM (Structure-from-Motion):** deducir poses y nube de puntos a partir de fotos.
- **MVS (Multi-View Stereo):** densificar la reconstrucción usando varias vistas.
- **NeRF:** red que aprende una escena 3D a partir de fotos.
- **Gaussian Splatting:** reconstrucción con "manchas" gaussianas; rápida y de calidad.
- **Shape completion:** completar una forma parcial con IA.
- **Inpainting:** rellenar huecos (en 2D o 3D).
- **Marching Cubes:** algoritmo que convierte una función implícita en malla.
- **Poisson reconstruction:** reconstruir superficie cerrada desde nube de puntos.
- **Chamfer distance / IoU / F-score:** métricas para comparar formas 3D.
- **Red neuronal / pesos / entrenamiento / pérdida (loss):** ver sección 2.
- **Dataset / train / validación / test:** datos para entrenar y medir.
- **GPU:** tarjeta gráfica; acelera el entrenamiento.
- **Fine-tuning:** ajustar un modelo ya entrenado a tu caso.
- **Modelo generativo:** red que crea contenido nuevo.
- **Laminador (slicer):** programa (Cura, PrusaSlicer) que convierte el STL en instrucciones para la impresora.
- **PyTorch / Open3D / Trimesh / COLMAP / SAM / Blender / MeshLab / Gradio:** ver sección 4.
- **Pipeline:** cadena de etapas encadenadas.
- **Ground truth:** la respuesta correcta conocida, contra la que mides.

---

## 15. Resumen en una página

- El proyecto convierte **fotos → modelo 3D → reparación → STL imprimible**.
- En 3D, la forma se guarda como **nube de puntos**, **malla** (triángulos) o **función implícita (SDF)**; para imprimir hace falta una **malla watertight** en formato **STL**.
- La **IA** del proyecto está en la **etapa 2 (reconstrucción)** y la **etapa 3 (reparación)**; el resto se hace con **herramientas existentes** (SAM, COLMAP, Open3D, MeshLab, Gradio).
- Herramientas base: **Python + PyTorch** para IA, **Open3D/Trimesh/Blender/MeshLab** para 3D, **Colab/GitHub** para trabajar.
- Se **entrena** con **datasets** (ShapeNet, Fantastic Breaks, CO3D...) usando **GPU**, partiendo a menudo de **modelos preentrenados** (fine-tuning).
- El éxito se **mide** con métricas (**Chamfer**, **IoU**) frente a un **ground truth**.
- Plan: aprender 3D con Blender/MeshLab → Open3D → PyTorch → tu etapa → reproducir un repo antes de innovar.
