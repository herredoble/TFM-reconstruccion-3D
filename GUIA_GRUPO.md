# Guía del grupo — TFM Reconstrucción 3D

**Entrega: 15 de septiembre de 2026**
**Repo:** https://github.com/herredoble/TFM-reconstruccion-3D

---

## Qué es este proyecto

Construimos un pipeline completo que transforma **fotos de un objeto roto en un archivo STL imprimible en 3D**. Está dividido en 5 etapas. Las etapas 2 y 3 son el núcleo de inteligencia artificial; las demás usan herramientas existentes.

```
Fotos → [E1 preproceso] → PNGs limpios → [E2 reconstrucción IA] → Nube de puntos rota
      → [E3 reparación IA] → Malla completa → [E4 STL] → archivo imprimible → [E5 app]
```

---

## Quién hace qué

| Persona | Etapa | Qué hace |
|---------|-------|----------|
| **Álvaro** | E2 arquitectura | Decide el método de reconstrucción (NeRF vs feed-forward). **Urgente esta semana.** |
| **Almu** | E1 + E2 implementación | Pipeline de juguete: fotos sintéticas de una taza → nube de puntos con nerfstudio |
| **Luis** | E2 métricas | Implementar Chamfer Distance y F-Score. Luego, asegurar que E2 entrega en el formato que espera E3 |
| **Rocío** | E3 modelo | Elegir y entrenar el baseline de shape completion (PCN como punto de partida) |
| **Raquel** | E3 datos | Datos listos — ver sección más abajo |

---

## Las 5 etapas en detalle

### E1 — Preprocesado de imágenes
Recibe fotos del objeto roto. Elimina el fondo con SAM (Meta), estima la posición
de la cámara en cada foto con COLMAP.
**Entrega a E2:** N imágenes PNG recortadas + `cameras.json`

### E2 — Reconstrucción 3D ⭐
A partir de las imágenes reconstruye la geometría del objeto en 3D.
Dos opciones en estudio: **nerfacto** (entrena por objeto, necesita poses de cámara,
más controlable) o **Zero123** (red preentrenada, inferencia rápida, menos precisa).
Álvaro decide esta semana. Su decisión desbloquea a Almu y Luis.
**Entrega a E3:** nube de puntos `.npy` de 2.048 puntos, puede tener huecos donde estaba la rotura

### E3 — Reparación generativa ⭐
Recibe la nube rota y la completa. Es *shape completion*: la red aprende a predecir
la parte que falta. Candidatos: PCN (más sencillo, empezar aquí), PoinTr (estado del arte), SnowFlakeNet.
**Entrega a E4:** malla 3D completa `.obj` o `.ply`

### E4 — Generación del STL
Convierte la malla en un `.STL` válido para imprimir: cerrar agujeros (*watertight*),
reparar normales, simplificar. Herramientas: Open3D, MeshLab, trimesh.
**Entrega a E5:** `.STL` watertight

### E5 — Aplicación
Une las 4 etapas en una demo usable. El usuario sube fotos y descarga el STL.
Herramienta recomendada: Gradio.

---

## Los datos que hay listos (en Google Drive del grupo)

| Carpeta en Drive | Qué contiene | Para qué |
|------------------|--------------|----------|
| `shapenet_limpias/` | 2.170 modelos 3D de vasijas (.ply) | Entrenar E2 y E3 |
| `objaverse_limpias/` | 197 modelos 3D de vasijas (.ply) | Complemento de entrenamiento |
| `fantastic_breaks_procesado/` | **61 pares (roto, completo) en .npy** | **Entrenar E3 directamente** |

Los datos **nunca van a GitHub** (son demasiado pesados). Solo van a Drive.
GitHub es solo para código y documentación.

### Formato de los datos de E3 (para Rocío)

Cada par son dos archivos `.npy`. Se cargan así:

```python
import numpy as np, torch

roto     = torch.from_numpy(np.load("00_00002_roto.npy"))      # shape (2048, 3)
completo = torch.from_numpy(np.load("00_00002_completo.npy"))  # shape (2048, 3)
```

- Shape: `(2048, 3)` — 2.048 puntos, coordenadas XYZ
- Dtype: float32
- Normalización: centrado en el origen, escalado a esfera unidad

Si el modelo necesita más datos, el script `Scripts/preprocesar_fantastic_breaks.py`
puede generar hasta 150 pares. Díselo a Raquel.

---

## Cómo trabajar: GitHub, Drive y Colab

### GitHub — para el código

**Qué va en GitHub:** scripts `.py`, notebooks `.ipynb`, documentación `.md`.
**Qué NO va:** datasets, modelos entrenados, archivos `.ply/.stl/.obj`. Eso va en Drive.

**La regla de oro:** nadie escribe directamente en `main`.
Cada tarea va en su propia rama y entra al proyecto por un Pull Request.

**Con GitHub Desktop (sin comandos):**
1. Abre GitHub Desktop y clona el repo si no lo tienes
2. Antes de empezar: **Fetch origin → Pull origin** (traer lo último)
3. Crea una rama: **Current Branch → New Branch** → nómbrala `etapa3/pcn-baseline`
4. Trabaja, guarda cambios: botón **Commit** (escribe qué hiciste) → **Push origin**
5. Cuando esté listo: **Create Pull Request** → asigna a alguien para que lo revise

**Nombres de rama:**
```
etapa2/nerfacto-shapenet
etapa3/pcn-baseline
etapa4/watertight-open3d
docs/actualizar-contratos
```

### Google Drive — para los datos

Todos los datasets y checkpoints de modelos entrenados van aquí.
Cuando entrenes en Colab, configura que los checkpoints se guarden en Drive
cada N épocas — si la sesión se corta (ocurre a las ~12h), no pierdes nada.

### Google Colab — para entrenar

Colab da GPU gratis (T4, ~16 GB VRAM). Imprescindible para E2 y E3.

Flujo recomendado:
1. Escribes el código en local y lo subes a GitHub
2. En Colab: clonas el repo + montas Drive
3. Entrenas — los checkpoints se guardan en Drive automáticamente
4. Al terminar: commit a GitHub de los scripts actualizados y métricas en CSV

```python
# En Colab: montar Drive
from google.colab import drive
drive.mount('/content/drive')

# Clonar el repo
!git clone https://github.com/herredoble/TFM-reconstruccion-3D.git
```

---

## Cómo mantener los documentos actualizados con IA

El proyecto tiene tres archivos que actúan como memoria del grupo:
- `PLANIFICACION.md` — estado de todas las tareas
- `NOTAS_Y_HALLAZGOS.md` — resultados técnicos, errores, decisiones
- `Documentacion/TFM_11_Contratos_Interfaz.md` — formato exacto entre etapas

Para mantenerlos al día sin esfuerzo, usad **Claude Code**:

**Instalación (una vez):**
```bash
# Necesitas Node.js (https://nodejs.org)
npm install -g @anthropic-ai/claude-code
```

**Uso diario:**
```bash
cd tfm-reconstruccion-3D   # entrar en la carpeta del repo
claude                      # abrirlo
```

La IA lee todos los archivos del repo automáticamente y tiene contexto completo
del proyecto. Ejemplos de lo que puedes pedirle:

```
"¿Qué tengo que hacer yo (Rocío) esta semana?"

"He entrenado PCN, loss final 0.12, Chamfer Distance 0.045.
 Actualiza PLANIFICACION.md y NOTAS_Y_HALLAZGOS.md con esto y haz commit."

"Hay un error al cargar los .npy, ayúdame a arreglarlo."
```

Ella edita los archivos, hace el commit y sube a GitHub. No hace falta saber Git.

**Sin instalar nada:** entra en https://claude.ai, crea un proyecto, sube
`PLANIFICACION.md`, `NOTAS_Y_HALLAZGOS.md` y `TFM_11_Contratos_Interfaz.md`.
Funciona igual pero los cambios no se guardan solos en el repo.

---

## Por dónde empieza cada persona ahora mismo

### Rocío
1. Descarga `fantastic_breaks_procesado/` de Drive (3 MB)
2. Lee cómo se cargan los datos en la sección de arriba
3. Investiga PCN como baseline — es el más sencillo para empezar
4. Primer objetivo: que el pipeline datos → entrenamiento → métricas funcione, aunque el resultado sea malo

### Álvaro
1. Decide esta semana: **nerfacto o Zero123**
2. Cuando decidas, actualiza `Documentacion/TFM_11_Contratos_Interfaz.md` con el método
3. Eso desbloquea a Almu y Luis

### Almu
1. Mientras Álvaro decide, monta el pipeline de juguete:
   - Instala nerfstudio en Colab
   - Genera renders sintéticos de una taza de ShapeNet con Blender
   - Pásalos por nerfstudio y exporta la nube de puntos
2. No tiene que ser perfecto — el objetivo es que el flujo funcione

### Luis
1. Implementa Chamfer Distance y F-Score (están en los repos de PoinTr y PCN)
2. Cuando Álvaro decida el método, define con él el formato exacto de salida de E2

---

## Decisiones urgentes esta semana

| Qué | Quién | Por qué es urgente |
|-----|-------|-------------------|
| Método E2: nerfacto vs Zero123 | Álvaro | Bloquea a Almu y Luis |
| Reunión para cerrar contrato E2→E3 | Todo el grupo | Sin esto la integración falla |
| Fijar día del sync semanal | Todo el grupo | 30 min/semana evita que todo se desincronice en agosto |

El contrato E2→E3 ya está propuesto en `Documentacion/TFM_11_Contratos_Interfaz.md`.
Solo falta que todos lo confirméis en una reunión rápida.
