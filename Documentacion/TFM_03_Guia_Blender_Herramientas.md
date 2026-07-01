# Guía de Blender y herramientas 3D para el TFM

> Manual práctico desde la instalación hasta saber usarlas.
> Pensado para quien nunca ha tocado un programa 3D.
> Raquel Roca · Junio 2026

---

## 0. ¿Qué herramientas necesitas y para qué?

En el proyecto hay dos "mundos": el del **código** (Python, Open3D, nerfstudio... que ya vimos) y el de las **herramientas visuales de escritorio**, que usas con el ratón para ver y preparar modelos. Esta guía cubre las visuales:

| Herramienta | Para qué la usarás en el TFM | ¿Imprescindible? |
|-------------|------------------------------|------------------|
| **Blender** | Ver modelos 3D, prepararlos, **renderizar fotos sintéticas** (etapa 1), hacer figuras bonitas para la memoria, exportar STL | Sí (la principal) |
| **MeshLab** | **Reparar mallas**: cerrar agujeros, hacerlas *watertight*, simplificar, limpiar (etapa 4) | Sí |
| **Laminador** (Cura o PrusaSlicer) | Abrir el STL final y comprobar/preparar la **impresión 3D** real | Solo si imprimís (P2) |

Las tres son **gratuitas**. Empieza por Blender.

---

## 1. BLENDER

### 1.1 Qué es
**Blender** es un programa gratuito y muy potente para crear, editar y visualizar gráficos 3D (lo usan desde estudiantes hasta estudios de cine). En tu TFM no harás animación: lo usarás sobre todo para **abrir modelos 3D y mirarlos**, **generar imágenes** de un objeto desde varios ángulos y **exportar/convertir** formatos.

### 1.2 Instalación
1. Ve a la web oficial: `https://www.blender.org/download/`
2. Descarga la versión **LTS** (Long Term Support: la más estable) para **Windows**.
3. Ejecuta el instalador y siguiente-siguiente-finalizar. No necesita configuración especial.
4. Ábrelo. Al arrancar verás una pantalla de bienvenida; haz clic fuera de ella para entrar.

> **Requisitos:** Blender va mejor con una tarjeta gráfica decente, pero para *ver* modelos y *renderizar* objetos pequeños funciona en cualquier portátil moderno.

### 1.3 La interfaz por primera vez (sin asustarse)
Al abrir, ves una escena con un **cubo** en el centro. Las zonas principales:

- **Viewport 3D (el centro):** la ventana donde ves la escena en 3D. Es donde pasarás el 90% del tiempo.
- **Outliner (arriba a la derecha):** la lista de todo lo que hay en la escena (objetos, cámara, luz).
- **Properties (abajo a la derecha):** paneles con todas las opciones (render, materiales, etc.).
- **Barra de menús (arriba):** `File`, `Edit`, `Render`, etc.

> Consejo: lo único que necesitas dominar al principio es **moverte por el viewport** (1.4) e **importar/ver un modelo** (1.5-1.6). Lo demás puede esperar.

### 1.4 Moverte por la escena (¡lo más importante!)
Con el ratón sobre el viewport:

- **Orbitar (girar alrededor):** mantén pulsada la **rueda del ratón** (botón central) y mueve.
- **Desplazar (pan):** **Shift + botón central** y mueve.
- **Zoom:** gira la **rueda del ratón**.
- **Vistas rectas con el teclado numérico:** `1` = frente, `3` = lado, `7` = arriba, `0` = vista desde la cámara. (Si tu portátil no tiene teclado numérico, actívalo en `Edit → Preferences → Input → Emulate Numpad`.)

> Practica 2 minutos: orbita, acércate y aléjate del cubo. Cuando te muevas con soltura, todo lo demás es fácil.

### 1.5 Importar un modelo 3D
1. **Borra el cubo** de ejemplo: haz clic en él (se pone un borde naranja) y pulsa `X` o `Supr`.
2. Menú **`File → Import`** y elige el formato de tu archivo: `Wavefront (.obj)`, `Stanford (.ply)` o `STL (.stl)` (los más comunes en el proyecto).
3. Busca tu archivo y dale a *Import*.
4. Aparece tu objeto. Si no lo ves, pasa el ratón por el viewport y pulsa la tecla **`Inicio` (Home)**: encuadra todo en pantalla. (O `View → Frame All`.)

### 1.6 Ver el objeto: sombreado y la malla de triángulos
Arriba a la derecha del viewport hay **cuatro bolitas** (modos de sombreado). De izquierda a derecha:

- **Wireframe:** solo las aristas (ves la "red" de triángulos por dentro).
- **Solid:** sólido gris (el más cómodo para mirar la forma). **Usa este por defecto.**
- **Material Preview / Rendered:** con colores y luces (más bonito, más lento).

Para **ver los triángulos de la malla** (entender el concepto de la guía):
1. Selecciona el objeto y pulsa **`Tab`** para entrar en **Modo Edición**.
2. Verás todos los vértices y triángulos que forman la superficie.
3. Pulsa `Tab` de nuevo para volver al **Modo Objeto**.

> **Modo Objeto** = mover/colocar objetos enteros. **Modo Edición** = tocar los vértices/caras de un objeto. Se alternan con `Tab`.

### 1.7 Operaciones básicas (mover, rotar, escalar)
En Modo Objeto, con el objeto seleccionado:
- **Mover:** tecla `G` (grab), mueve el ratón, clic para confirmar.
- **Rotar:** tecla `R`.
- **Escalar (tamaño):** tecla `S`.
- (Puedes pulsar `X`, `Y` o `Z` tras `G`/`R`/`S` para restringir a un eje.)

### 1.8 Exportar a STL (o convertir entre formatos)
1. Selecciona el objeto.
2. Menú **`File → Export → STL (.stl)`** (o el formato que quieras: OBJ, PLY...).
3. Elige carpeta y nombre, *Export*.

> Esto convierte Blender en un **conversor de formatos** muy útil: importas un `.ply` y exportas un `.stl`, por ejemplo.

### 1.9 (Para el proyecto) Generar imágenes de un objeto desde varios ángulos
Esto es **directamente útil para la etapa 1**: crear el "dataset sintético" de fotos a partir de un modelo 3D. Dos formas:

**A) Manual (para entender el concepto):**
1. En el Outliner verás una **Camera** y una **Light**. Selecciona la cámara, muévela (`G`) alrededor del objeto.
2. Pulsa `0` (numpad) para ver lo que capta la cámara.
3. Menú **`Render → Render Image`** (o `F12`). Se abre la imagen renderizada.
4. En esa ventana, `Image → Save As` para guardarla. Repite moviendo la cámara para tener varios ángulos.

**B) Automático con un script (avanzado, pero es lo que de verdad usaríais):**
Blender tiene una pestaña **Scripting** (arriba). Ahí puedes pegar código Python que rota la cámara y renderiza muchas vistas de golpe:

```python
import bpy, math, os

# --- AJUSTA ESTAS RUTAS ---
ruta_modelo   = r"C:/ruta/a/tu/modelo.obj"
carpeta_salida = r"C:/ruta/salida/"
n_vistas = 12        # cuántas fotos alrededor del objeto
radio    = 3.0       # distancia de la cámara al objeto

# 1) Vaciar la escena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 2) Importar el modelo (usa wm.stl_import o wm.ply_import si no es .obj)
bpy.ops.wm.obj_import(filepath=ruta_modelo)

# 3) Crear una cámara que siempre mire al centro
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
objetivo = bpy.data.objects.new("Objetivo", None)   # punto central
bpy.context.collection.objects.link(objetivo)
seguir = cam.constraints.new(type='TRACK_TO')       # "mira siempre al centro"
seguir.target = objetivo

# 4) Una luz para que se vea
luz_data = bpy.data.lights.new("Luz", type='SUN')
luz = bpy.data.objects.new("Luz", luz_data)
bpy.context.collection.objects.link(luz)
luz.location = (5, 5, 8)

# 5) Dar la vuelta al objeto renderizando n vistas
for i in range(n_vistas):
    ang = 2 * math.pi * i / n_vistas
    cam.location = (radio*math.cos(ang), radio*math.sin(ang), 1.2)
    bpy.context.scene.render.filepath = os.path.join(carpeta_salida, f"vista_{i:02d}.png")
    bpy.ops.render.render(write_still=True)

print("¡Listo! Imágenes guardadas en", carpeta_salida)
```

> No hace falta entenderlo línea a línea ahora. La idea: **un script coloca la cámara en círculo alrededor del objeto y guarda una foto en cada posición**. Así generas decenas de imágenes con sus ángulos conocidos, perfectas para alimentar la etapa 2.

---

## 2. MESHLAB

### 2.1 Qué es y para qué
**MeshLab** es un programa gratuito especializado en **procesar y reparar mallas**. Es tu herramienta de la **etapa 4**: cuando una malla tiene agujeros o defectos, MeshLab la limpia y la deja *watertight* (cerrada, imprimible).

### 2.2 Instalación
1. Web oficial: `https://www.meshlab.net/`
2. Descarga la versión de **Windows** e instálala (siguiente-siguiente).

### 2.3 Importar y ver una malla
1. **`File → Import Mesh`** y elige tu `.ply`, `.obj` o `.stl`.
2. Navegación parecida a Blender: **arrastrar con botón izquierdo** = orbitar, **rueda** = zoom.

### 2.4 Reparar la malla (lo importante)
MeshLab trabaja aplicando **filtros** (menú `Filters`). Los más útiles para imprimibilidad:

- **Cerrar agujeros:** `Filters → Remeshing, Simplification and Reconstruction → Close Holes`. Rellena los huecos de la superficie.
- **Quitar trozos sueltos:** `Filters → Cleaning and Repairing → Remove Isolated Pieces` (elimina fragmentos basura no conectados).
- **Recalcular normales:** `Filters → Normals, Curvatures and Orientation → Re-Orient all faces coherently` (arregla la orientación "dentro/fuera").
- **Reconstrucción de superficie cerrada:** `Filters → Remeshing... → Surface Reconstruction: Screened Poisson`. Si partes de una nube de puntos o una malla muy rota, esto genera una superficie nueva y cerrada (igual que la Poisson de Open3D, pero con ratón).

> Tras reparar, comprueba en `Render → Show Box Corners` o en las estadísticas que no quedan agujeros. La regla: **cerrada y sin trozos sueltos = imprimible.**

### 2.5 Simplificar (si pesa demasiado)
Si la malla tiene millones de triángulos: `Filters → Remeshing... → Simplification: Quadric Edge Collapse Decimation`. Le dices a cuántas caras quieres bajar y reduce manteniendo la forma.

### 2.6 Exportar
**`File → Export Mesh As`** y elige **STL** para la impresión. Listo.

---

## 3. EL LAMINADOR (Cura o PrusaSlicer) — solo si vais a imprimir

### 3.1 Para qué
Un **laminador (slicer)** convierte tu `.STL` en las instrucciones que entiende la impresora 3D (el "G-code"), cortando el objeto en capas. También **avisa de problemas** de imprimibilidad. Aunque no tengáis impresora, abrir aquí el STL es una buena **prueba final** de que el modelo es válido.

### 3.2 Instalación y uso básico
1. Descarga **UltiMaker Cura** (`https://ultimaker.com/software/ultimaker-cura/`) o **PrusaSlicer** (`https://www.prusa3d.com/page/pruslicer/`). Ambos gratis.
2. **`Abrir archivo`** y carga tu `.stl`.
3. Verás el objeto sobre una "cama" de impresión. Si aparece en gris/raro o avisa de errores, la malla no es válida (vuelve a MeshLab).
4. Botón **`Slice` / `Rebanar`**: genera la vista por capas y te dice tiempo y material estimados. Si llega aquí sin quejarse, **tu STL es imprimible**. 🎉

---

## 4. Flujo recomendado: cómo encaja todo

Un recorrido típico de trabajo con estas herramientas:

1. **Blender** — abrir un modelo 3D del dataset, mirarlo, entender su malla; y/o **renderizar imágenes** desde varios ángulos para la etapa 1.
2. *(El código hace las etapas 2 y 3: reconstrucción y reparación con IA.)*
3. **MeshLab** — coger la malla que sale de la IA y **repararla** hasta dejarla *watertight* (etapa 4).
4. **Blender** otra vez — opcional, para una **render bonita** del resultado para la memoria/slides.
5. **Cura/PrusaSlicer** — abrir el STL final y comprobar (o imprimir) (P2).

> Regla práctica: **Blender para ver y generar imágenes; MeshLab para reparar; el laminador para verificar la impresión.** Open3D/Trimesh (código) hacen lo mismo que MeshLab pero **automatizado** dentro del pipeline — las herramientas visuales son para entender, probar y presentar.

---

## 5. Cómo aprender (recursos y orden)

1. **Blender — "Donut tutorial" de Blender Guru** (YouTube): el tutorial de iniciación más famoso del mundo. No necesitas hacerlo entero; con la primera parte ya te manejas por la interfaz.
2. Practica con un modelo del proyecto: impórtalo, gíralo, entra en Modo Edición para ver la malla, expórtalo a STL.
3. **MeshLab:** busca "MeshLab close holes" / "MeshLab Poisson reconstruction"; son vídeos cortos y van al grano.
4. No intentes dominar Blender entero: **solo necesitas** importar, navegar, ver la malla, exportar y (opcional) renderizar vistas. Lo demás, cuando haga falta.

> Recuerda: estas herramientas son **medios**, no el fin. El núcleo del TFM sigue siendo el código de las etapas 2 y 3; Blender y MeshLab te ayudan a **ver, preparar y presentar**.
