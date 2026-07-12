# TFM_13 — Estado actual del proyecto y arranque para cada persona

> Documento de puesta al día para todo el grupo.
> Qué hay hecho, qué tiene que hacer cada uno, cómo usar GitHub y cuándo usar Colab.
> Raquel Roca · 12 jul 2026.

---

## Lo que hay hecho hasta hoy

Raquel ha trabajado estas semanas preparando la base de datos y la infraestructura
del proyecto. Esto es lo que ya no hace falta que haga nadie más:

### Datasets listos (en Google Drive del grupo)

| Dataset | Qué es | Dónde está | Para qué sirve |
|---------|--------|------------|----------------|
| **ShapeNet** | 2.170 modelos 3D de vasijas (mug, bowl, bottle, jar, can) limpios y normalizados | Drive → `shapenet_limpias/` | Entrenar E2 y E3 |
| **Objaverse** | 197 tazas y cuencos limpios | Drive → `objaverse_limpias/` | Complemento de entrenamiento |
| **Fantastic Breaks procesado** | 61 pares (roto → completo) listos para entrenar, formato .npy | Drive → `fantastic_breaks_procesado/` | **Entrenar E3 directamente** |

Los datos de Fantastic Breaks son el trabajo más importante para E3: 61 escaneos 3D
de objetos reales rotos emparejados con su versión completa, ya convertidos al formato
que entienden las redes de shape completion (2.048 puntos, numpy float32).

### Repositorio GitHub

El repositorio del grupo está en: `https://github.com/herredoble/TFM-reconstruccion-3D`

Ya tiene:
- `Scripts/` — todos los scripts de descarga y preprocesado
- `Documentacion/` — todos los documentos del proyecto (incluyendo este)
- `NOTAS_Y_HALLAZGOS.md` — bitácora técnica del proyecto
- `PLANIFICACION.md` — estado de las tareas y cronograma

---

## Las 5 etapas del proyecto

El pipeline completo transforma **fotos de un objeto roto → archivo STL imprimible**.
Cada etapa es un módulo independiente con una entrada y una salida definida.

```
[Fotos] → E1 → [PNGs recortados] → E2 → [Nube de puntos rota] → E3 → [Malla reparada] → E4 → [STL] → E5 → [App]
```

### E1 — Captura y preprocesado de imágenes
**Qué hace:** recibe fotos del objeto y las prepara para la reconstrucción.
Detecta el objeto, elimina el fondo (con SAM de Meta), estima la posición de la
cámara en cada foto.
**Qué entrega:** N imágenes PNG recortadas + `poses.json` con la posición de cada cámara.
**Nivel de IA:** medio (visión por computador, no deep learning generativo).

### E2 — Reconstrucción 3D ⭐ (núcleo de IA)
**Qué hace:** a partir de las imágenes reconstruye la geometría 3D del objeto.
Puede usar NeRF (nerfacto de nerfstudio) o un modelo feed-forward (Zero123).
La decisión entre estas dos opciones la toma Álvaro esta semana.
**Qué entrega:** nube de puntos `.npy` de 2.048 puntos, normalizada, con huecos donde
estaba la parte rota.
**Nivel de IA:** alto. Es el módulo más técnico del pipeline.

### E3 — Reparación generativa ⭐ (núcleo de IA)
**Qué hace:** recibe la nube de puntos rota y la completa. Es un problema de
*shape completion*: la red aprende a "adivinar" la parte que falta.
Candidatos de modelos: **PoinTr**, **PCN**, **SnowFlakeNet**.
**Qué entrega:** malla 3D completa `.obj` o `.ply` sin huecos.
**Nivel de IA:** muy alto. Deep learning generativo en 3D. Los datos para entrenarla
ya están preparados (ver Drive).
**Datos listos:** 61 pares reales de entrenamiento en `fantastic_breaks_procesado/`.

### E4 — Generación del STL imprimible
**Qué hace:** toma la malla reparada y la convierte en un archivo `.STL` válido para
imprimir: cerrar agujeros (watertight), reparar normales, simplificar.
Herramientas: Open3D, MeshLab, trimesh.
**Qué entrega:** archivo `.STL` watertight + `report.json` con la validación.
**Nivel de IA:** bajo. Geometría computacional, no aprendizaje.

### E5 — Aplicación end-to-end
**Qué hace:** une las 4 etapas en una app usable. El usuario sube fotos y descarga el STL.
Herramienta candidata: Gradio (muy sencillo para prototipos de ML).
**Qué entrega:** la demo funcional del proyecto.
**Nivel de IA:** bajo. Más de ingeniería de software.

---

## Por dónde empieza cada persona

### Rocío — E3 (Reparación)
Tienes los datos listos. Puedes empezar a entrenar hoy.

**Paso 1:** descarga `fantastic_breaks_procesado/` de Drive. Son 122 archivos `.npy`,
3 MB en total. Cada par se carga así:

```python
import numpy as np, torch

roto     = torch.from_numpy(np.load("00_00002_roto.npy"))      # (2048, 3)
completo = torch.from_numpy(np.load("00_00002_completo.npy"))  # (2048, 3)
```

**Paso 2:** investiga los tres candidatos de modelo y elige el baseline:
- **PCN** (Point Completion Network) — el más simple, buen punto de partida
- **PoinTr** — estado del arte, más complejo de implementar
- **SnowFlakeNet** — buen equilibrio entre calidad y coste

**Paso 3:** primer entrenamiento en Colab con PCN sobre los 61 pares.
No esperes buen resultado con 61 pares — el objetivo es que el pipeline
(datos → entrenamiento → métricas) funcione de punta a punta.

Toda la información del formato de los datos está en `TFM_12_Datos_E3_Rocio.md`.
Si 61 pares no son suficientes para que converja, avisa a Raquel y regeneramos
con más clases (hasta 150 pares disponibles en el dataset).

---

### Álvaro — E2 (Reconstrucción) — decisión urgente

**Esta semana** tienes que decidir el método de E2. De esto dependen Almu y Luis.

| Opción | Cómo funciona | Ventaja | Desventaja |
|--------|---------------|---------|------------|
| **nerfacto** (NeRF) | entrena una red pequeña por objeto a partir de N fotos con poses conocidas | No necesita dataset previo; funciona con 8-20 fotos | Tarda minutos por objeto en inferencia; necesita poses de cámara |
| **Zero123 / LRM** | red ya entrenada que predice la 3D a partir de 1-4 fotos | Inferencia instantánea | Requiere fine-tuning; calidad inferior en objetos muy específicos |

**Recomendación:** empieza con nerfacto para el P0 (más documentado, más controlable).
Zero123 como P1 si hay tiempo.

Cuando decidas, actualiza `TFM_11_Contratos_Interfaz.md` con el método elegido.
Eso cierra el contrato E1→E2 y desbloquea a Almu.

---

### Almu — E1 + E2 (pipeline de captura y reconstrucción)

Mientras Álvaro decide el método, tu primera tarea es el **pipeline de juguete**:
tomar 5-8 fotos sintéticas de una taza de ShapeNet y reconstruirla con nerfstudio.

**Paso 1:** instala nerfstudio en Colab siguiendo `TFM_02_Guia_Completa.md`.
Los mensajes rojos al instalar son avisos, no errores (hallazgo H3 del proyecto).

**Paso 2:** genera renders sintéticos de una taza de ShapeNet con Blender
(instrucciones en `TFM_03_Guia_Blender_Herramientas.md`).

**Paso 3:** pasa esas imágenes por nerfstudio y exporta la nube de puntos.

El objetivo no es calidad: es que el flujo E1→E2→nube funcione sobre un ejemplo
controlado antes de meter fotos reales.

---

### Luis — Métricas e integración E2→E3

Tu trabajo define si el modelo funciona o no. Sin métricas claras no sabemos
si estamos mejorando.

**Paso 1:** implementa las dos métricas estándar de shape completion:
- **Chamfer Distance (CD):** distancia media entre la nube predicha y la real. Cuanto menor, mejor.
- **F-Score a umbral τ:** porcentaje de puntos que caen dentro de una distancia τ. Cuanto mayor, mejor.

Estas métricas están documentadas en `TFM_02_Guia_Completa.md`. Hay implementaciones
de referencia en los repositorios de PoinTr y PCN.

**Paso 2:** una vez que Álvaro cierre el método de E2, tú te encargas de que la
salida de E2 (nube de puntos) esté exactamente en el formato que espera E3.
El formato ya está acordado: `.npy` float32 shape `(2048, 3)`. Ver `TFM_11_Contratos_Interfaz.md`.

---

## GitHub: para qué sirve en este proyecto y cómo usarlo

### Por qué usamos GitHub y no solo Drive

Drive es para los **datos** (datasets pesados que no caben en Git).
GitHub es para el **código**: scripts, notebooks, documentación.

La diferencia clave: GitHub guarda el historial completo de cada cambio.
Si algo deja de funcionar, puedes ver exactamente qué cambió y volver atrás.
Con Drive no puedes hacer eso.

### La regla más importante

**Nadie escribe directamente en `main`.** Todo cambio va en una rama propia y
entra al proyecto a través de un *pull request* que revisa otra persona.

Esto evita el problema de "alguien rompió algo y no sé quién fue".

### Flujo en 4 pasos (con GitHub Desktop, sin comandos)

GitHub Desktop es una aplicación visual que hace todo esto con botones.
Descárgala en https://desktop.github.com — no hace falta aprender comandos.

**1. Antes de empezar a trabajar:** botón "Fetch origin" → "Pull origin".
Trae los cambios que hayan subido los demás desde la última vez.

**2. Crear tu rama:** "Current Branch" → "New Branch".
Nómbrala así: `etapa3/shape-completion-pcn` (etapa + descripción corta).
Una rama = un tema de trabajo. No mezcles cosas distintas en la misma rama.

**3. Guardar tus cambios:** cuando hayas hecho algo que funciona, botón "Commit".
El mensaje del commit debe explicar qué hiciste: `"E3: primer entrenamiento PCN, loss 0.08"`.
Luego "Push origin" para subir tu rama a GitHub.

**4. Pedir que lo revisen:** botón "Create Pull Request" → describe el cambio →
asigna como revisor a la persona responsable de tu etapa.
Cuando la otra persona lo aprueba, se fusiona con `main`.

### Qué va al repo y qué va a Drive

| Sube a GitHub | Va a Drive |
|---------------|------------|
| Scripts `.py` | Datasets (ShapeNet, Objaverse, Fantastic Breaks) |
| Notebooks `.ipynb` | Checkpoints de modelos entrenados (`.pt`, `.pth`) |
| Documentación `.md` | Archivos 3D (`.ply`, `.obj`, `.stl`) |
| Métricas en CSV | Cualquier cosa mayor de ~50 MB |
| `requirements.txt` | |

El `.gitignore` ya está configurado para bloquear los archivos que no deben subir.

### Nombres de rama que usamos

```
etapa1/segmentacion-sam
etapa2/nerfacto-shapenet
etapa3/pcn-baseline
etapa4/watertight-open3d
docs/actualizar-contratos
```

---

## Colab o local: cuándo usar cada uno

No son opciones excluyentes. Se usan para cosas distintas.

### Usa **Google Colab** para:
- **Entrenar modelos** (E2 y E3): Colab da GPU gratuita (T4, ~16 GB VRAM).
  Sin GPU el entrenamiento de una red de shape completion tardaría días.
- Probar código que necesita librerías difíciles de instalar (nerfstudio, PyTorch3D).
- Experimentos rápidos y exploración de datos.

**Limitación importante de Colab gratuito:** la sesión se corta a las ~12 horas
y pierdes todo lo que no hayas guardado en Drive. Solución: guardar checkpoints
en Drive cada N épocas.

### Usa **tu ordenador** para:
- Escribir y editar scripts `.py`.
- Commitar y hacer push a GitHub.
- Procesar datos pequeños (los scripts de Raquel funcionan en local sin GPU).
- Leer documentación y planificar.

### El flujo recomendado

```
1. Escribes el código en local (tu editor favorito)
2. Lo pruebas en local si no necesita GPU
3. Lo subes a GitHub (commit + push)
4. En Colab: git clone del repo + montar Drive + lanzar entrenamiento
5. Checkpoints y métricas → Drive
6. Resultados finales (scripts actualizados, CSVs de métricas) → commit a GitHub
```

Así el código siempre está en GitHub (con historial) y los datos pesados en Drive.

### ¿Colab Pro vale la pena?

Para este TFM probablemente no hace falta. La GPU T4 gratuita es suficiente para
entrenar PCN o PoinTr sobre 61 pares. Si los experimentos se alargan mucho (más de
12h continuadas) o necesitáis una GPU más potente para P1, planteadlo entonces.

---

## Próximas reuniones y decisiones críticas

Estas son las decisiones que están bloqueando el avance del grupo:

| Decisión | Quién | Urgencia |
|----------|-------|----------|
| Método E2: nerfacto vs Zero123 | Álvaro | Esta semana — desbloquea a Almu y Luis |
| Confirmar contrato E2→E3 en reunión | Todo el grupo | Esta semana — el formato está propuesto, solo falta acordarlo |
| Fijar día y hora del sync semanal | Todo el grupo | Esta semana |

Ver `TFM_11_Contratos_Interfaz.md` para los detalles del contrato E2→E3 propuesto.
Ver `PLANIFICACION.md` para el estado actualizado de todas las tareas.
