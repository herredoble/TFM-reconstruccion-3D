# TFM — Tema 13: Reconstrucción 3D y reimpresión de objetos a partir de fotos

> Documento de propuesta, viabilidad y planificación para el grupo (5 integrantes).
> Autora de la idea: Raquel Roca · Junio 2026 · Entrega: 15 de septiembre de 2026

---

## 1. La idea en una frase

Una aplicación que, a partir de varias **fotos** de un objeto, **reconstruye su modelo 3D**, **rellena con IA las partes dañadas o que faltan**, y genera un archivo **STL listo para imprimir** en una impresora 3D.

El flujo completo:

**Fotos multivista** → **reconstrucción 3D** (fotogrametría o deep learning) → **reparación/completado generativo** de partes dañadas → **exportar STL imprimible** (watertight).

El elemento diferenciador frente a un escáner 3D normal es la **reparación automática de las partes dañadas**.

---

## 2. El proyecto dividido en 5 etapas

El *pipeline* completo se divide de forma natural en 5 etapas. Cada una es lo bastante densa como para ser un trabajo entero por sí sola — lo que, con un grupo de 5, encaja como **una etapa por persona**.

| # | Etapa | Qué hace | Dificultad | Componente principal |
|---|-------|----------|------------|----------------------|
| 1 | **Captura y preprocesado** | Detección del objeto, segmentación del fondo, estimación de pose de cámara, normalización de iluminación | Media | Visión por computador |
| 2 | **Reconstrucción 3D** | De las imágenes a nube de puntos / malla (fotogrametría SfM+MVS, o deep learning: NeRF, Gaussian Splatting, image-to-3D) | Alta | Deep learning / visión |
| 3 | **Reparación / completado** | Modelo generativo que rellena las partes dañadas (shape completion / inpainting 3D) | Muy alta | Deep learning generativo |
| 4 | **Generación del STL** | Convertir la malla en `.STL` válido: cerrar (watertight), reparar normales, simplificar, asegurar imprimibilidad | Media-baja | Geometría computacional |
| 5 | **App end-to-end** | Interfaz: subir fotos, ver modelo, descargar STL, enviar a impresora; integración de todo | Media | Producto / MLOps |

---

## 3. Viabilidad de hacer las 5 etapas (siendo 5 en el grupo)

**Siendo 5 personas, el pipeline completo de 5 etapas SÍ es viable** — y de hecho es el reparto natural: **una etapa por integrante**. El "inviable" que se suele decir aplica a una persona sola; con un equipo, lo que cambia no es la cantidad de trabajo sino **dónde está el riesgo**.

### Lo que hace viable el proyecto con 5 personas
- Cada integrante es **dueño de una etapa** y puede profundizar en ella (su propio mini-estado del arte y métricas).
- Las etapas se pueden **desarrollar en paralelo** una vez acordadas las interfaces.
- Cada persona tiene un **capítulo claro de la memoria** y una contribución defendible individualmente.

### Dónde está ahora el riesgo (y cómo mitigarlo)
1. **Integración y errores en cascada.** → **Mitigación:** definir las *interfaces* (formato exacto de datos entre etapas) en la **primera semana**; trabajar contra datos de prueba estandarizados.
2. **Acoplamiento temporal.** → **Mitigación:** cada etapa arranca con un *dataset de referencia* (entrada simulada) para no esperarse entre sí.
3. **Agosto.** Periodo de vacaciones en España; pactar disponibilidad para que la integración no caiga en hueco.

> **Veredicto:** con 5 personas, las 5 etapas son el alcance correcto. La clave del éxito no es el volumen de trabajo, sino **acordar las interfaces pronto y reservar tiempo de integración**.

---

## 4. Estrategia de ejecución: núcleo primero (MVP) y extensiones

En lugar de repartir las 5 etapas a igual profundidad, se **concentra el esfuerzo en las 2 etapas que aportan la IA del proyecto** (reconstrucción y reparación) y se resuelven las otras tres con **herramientas ya existentes**. Es el enfoque **MVP / "esqueleto andante"**: primero la versión mínima que funciona de punta a punta, y solo si sobra tiempo se amplía. Así siempre hay algo que funciona y las mejoras son aditivas.

### Qué es "núcleo" y qué no
| Etapa | ¿Núcleo? | Cómo abordarla en el MVP |
|-------|----------|--------------------------|
| 1. Captura / preprocesado | No | Herramientas existentes: **SAM** (segmentación) + **COLMAP** (pose). Apenas código propio |
| **2. Reconstrucción 3D** | **Sí** | Investigación propia (NeRF / Gaussian Splatting / image-to-3D) |
| **3. Reparación / completado** | **Sí** | Investigación propia (shape completion con DL) |
| 4. STL imprimible | No | Herramientas existentes: **Open3D / MeshLab** (Poisson + cerrar malla) |
| 5. App end-to-end | No | Un notebook o script que encadene todo; sin UI elaborada al principio |

> El TFM "de verdad" son las **etapas 2 y 3**. Las otras tres existen para poder mostrar el resultado de punta a punta; no hace falta innovar en ellas.

### Reparto de los 5 sobre el núcleo (2 – 2 – 1)
- **2 personas → Etapa 2** (reconstrucción): la más grande, aguanta dos.
- **2 personas → Etapa 3** (reparación): la más novedosa, también aguanta dos.
- **1 persona → "fontanería"**: etapas 1 + 4 + 5 con herramientas existentes + montaje del pipeline e integración (rol de pegamento/coordinación).

### Niveles de alcance (tiers)
- **P0 — Núcleo (objetivo de entrega).** Pipeline end-to-end sobre **una sola categoría de objetos**, con las etapas 2 y 3 propias y 1/4/5 con herramientas. *Es lo que tiene que estar sí o sí el 15 de septiembre.*
- **P1 — Mejoras si sobra tiempo.** Hacer "propia" alguna etapa auxiliar (p. ej. etapa 4 con reparación de malla aprendida, o etapa 1 con segmentación/pose propias); añadir **más categorías** de objetos; validar con **fotos reales** (CO3D/GSO) y no solo modelos sintéticos.
- **P2 — Lujo.** Etapa 5 como **app real** con interfaz e impresión, comparativa amplia de métodos, demo en vivo.

> **Regla de oro:** comprometerse en la propuesta **solo al P0**. P1 y P2 se mencionan como *"trabajo futuro / extensiones si el tiempo lo permite"*. El tiempo "de sobra" se reserva a propósito dejando P1/P2 al final como opcionales, en lugar de comprometerse a ellos desde el principio. Ventaja extra: es más fácil de defender ante el tutor ("priorizamos el componente de IA y dejamos extensiones identificadas").

---

## 5. Planificación temporal (10 jun → 15 sep 2026)

≈ **14 semanas**. Reparto **2-2-1** sobre el núcleo (sección 4). La redacción de la memoria es **continua** (cada uno documenta su parte desde el principio). El **núcleo P0 se congela el 16 de agosto**; lo posterior es evaluación, extensiones opcionales y redacción.

| Fase | Fechas | Sem. | Quién | Entregable / hito |
|------|--------|------|-------|-------------------|
| **0. Arranque común** | 10–21 jun | 1–2 | Todos | Estado del arte, alcance y categoría definidos; datasets descargados (**pedir ShapeNet YA**); repo y entorno común; **interfaces entre etapas acordadas** |
| **1. Desarrollo del núcleo en paralelo** | 22 jun – 2 ago | 3–8 | Reparto 2-2-1 | Etapas 2 y 3 propias; 1/4/5 con herramientas. **Hito ~17 jul**: demo por módulo |
| **2. Integración del núcleo (P0)** | 3–16 ago | 9–10 | Persona "fontanería" + todos | **Pipeline P0 completo foto → STL** funcionando; corrección de errores en cascada |
| **3. Evaluación + extensiones opcionales (P1/P2)** | 17–30 ago | 11–12 | Todos | Métricas (Chamfer, IoU, imprimibilidad), tablas; **extensiones solo si el P0 está sólido** |
| **4. Redacción y presentación** | 31 ago – 12 sep | 12–14 | Todos | Memoria final revisada, formato, slides de defensa |
| **5. Buffer + entrega** | 13–15 sep | 14 | Todos | Margen para imprevistos. **Entrega: 15 sep** |

**Hitos clave**
- **21 jun** — Cierre de alcance e interfaces (sin esto, la integración fracasa).
- **17 jul** — Demo intermedia: cada módulo vivo por separado.
- **16 ago** — **Núcleo P0 integrado y funcionando de punta a punta** (hito crítico: a partir de aquí, todo es mejora o pulido).
- **30 ago** — Congelado de experimentos y resultados.
- **12 sep** — Memoria lista; 13–15 sep solo buffer.

> ⚠️ **Aviso agosto:** la integración (fase 2) necesita a todo el equipo y cae en agosto. Pactad disponibilidad o adelantad lo posible a julio.

---

## 6. Bases de datos candidatas

### 6.1 Núcleo del TFM (reconstrucción + reparación)

| Dataset | Qué es | Licencia / acceso | Enlace |
|---------|--------|-------------------|--------|
| **ShapeNet** | ~51K modelos CAD por categorías. Estándar de comparación | Registro; solo no-comercial | https://shapenet.org/ · https://huggingface.co/datasets/ShapeNet/ShapeNetCore |
| **Objaverse / XL** | 800K–10M objetos con descripciones | Abierto | https://objaverse.allenai.org/ · https://huggingface.co/datasets/allenai/objaverse |
| **ABO (Amazon Berkeley Objects)** | ~8K mallas de productos | CC BY-NC 4.0 | https://amazon-berkeley-objects.s3.amazonaws.com/index.html |
| **⭐ Fantastic Breaks** | 150 objetos rotos ↔ completos (el caso ideal del TFM) | Abierto (investigación) | https://terascale-all-sensing-research-studio.github.io/FantasticBreaks/ |
| **Completion3D** | Benchmark parcial → completo (8 cat. ShapeNet) | Abierto | https://paperswithcode.com/dataset/completion3d |
| **Pix2Repair** | Restauración de forma desde imágenes | Abierto | https://arxiv.org/pdf/2305.18273 |

### 6.2 De fotos reales → 3D (multivista)

| Dataset | Qué es | Licencia / acceso | Enlace |
|---------|--------|-------------------|--------|
| **⭐ CO3D (Meta)** | 1,5M frames, ~19K vídeos, poses + nubes de puntos | Abierto | https://ai.meta.com/datasets/co3d-dataset/ |
| **Google Scanned Objects** | ~1.000 objetos escaneados + 847K imágenes RGB-D | Abierto | https://arxiv.org/abs/2203.11397 |
| **DTU** | Benchmark fotogrametría con ground-truth | Abierto | "DTU MVS dataset" |

### 6.3 STL imprimible

| Dataset | Qué es | Licencia / acceso | Enlace |
|---------|--------|-------------------|--------|
| **⭐ Thingi10K** | 10.000 modelos reales de impresión 3D (incluye mallas defectuosas) | Abierto | https://github.com/Thingi10K/Thingi10K |

> **Nota sobre ShapeNet:** requiere registro (nombre, tutor/PI, institución) y solo permite uso no comercial; la aprobación tarda días — pedirlo en la semana 1. Mientras llega, **Objaverse** y **ABO** son de acceso inmediato.

---

## 7. Flujo de datos entre etapas

Esta sección detalla qué dataset alimenta cada etapa, qué se extrae de él y en qué formato debe quedar para que la siguiente etapa lo pueda consumir. **Las interfaces entre etapas (columna "Formato de salida") son los contratos que el equipo debe acordar antes del 21 de junio.**

### 7.1 Diagrama de flujo

```
  DATASETS DE ENTRENAMIENTO           FLUJO DE INFERENCIA (demo real)
  ─────────────────────────           ────────────────────────────────

  Objaverse .glb (246)                Fotos del móvil (N imágenes)
    │ renderizar 16-36 vistas                    │
    ▼                                            ▼
  Imágenes sintéticas             ┌─────────────────────────┐
  + data augmentation  ──train──► │  ETAPA 1 — Captura      │ (SAM + COLMAP)
                                  └─────────────────────────┘
  CO3D cup/bowl/vase                           │
    │ fotos reales                    N imágenes sin fondo
    ▼                                + poses de cámara (.json)
  Validación E1 + E2  ──val────►              │
                                              ▼
  Objaverse .glb      ──train──► ┌─────────────────────────┐
  (renders + poses)              │  ETAPA 2 — Reconstrucción│
                                 └─────────────────────────┘
  CO3D                ──val────►              │
                                    Nube de puntos / malla
                                    de la taza ROTA (.ply)
                                              │
                                              ▼
  Objaverse .ply      ──train──► ┌─────────────────────────┐
  (rotura sintética)             │  ETAPA 3 — Reparación   │
  Fantastic Breaks    ──val────► └─────────────────────────┘
                                              │
                                    Malla 3D COMPLETA (.ply)
                                              │
                                              ▼
  Tazas_limpias .ply  ──test───► ┌─────────────────────────┐
  (191 no-watertight)            │  ETAPA 4 — STL          │ (Open3D/MeshLab)
  Thingi10K           ──test───► └─────────────────────────┘
                                              │
                                         .STL válido
                                              │
                                              ▼
                                       Impresora 3D
```

### 7.2 Tabla detallada por etapa

| Etapa | Dataset (rol) | Qué se extrae / genera | Formato de salida | Interfaz con la siguiente |
|-------|--------------|------------------------|-------------------|---------------------------|
| **1 — Captura** | CO3D cup/bowl/vase *(validación)* | Secuencias de fotos reales ya con poses y segmentación | N imágenes PNG sin fondo + `cameras.json` (intrínsecas + extrínsecas por vista) | E2 espera este formato exacto |
| **2 — Reconstrucción** | Objaverse .glb → renders *(train)*; CO3D *(val)* | Renders multivista (16-36 por modelo) con augmentation (fondo, ruido, luz) → pares (imágenes, modelo 3D ground-truth) | Nube de puntos `.ply` o malla `.obj` del objeto reconstruido | E3 espera nube de puntos normalizada (centrada, escala unidad) |
| **3 — Reparación** | Objaverse .ply → rotura sintética *(train)*; Fantastic Breaks *(val)* | Pares (modelo roto, modelo completo): cortar con plano aleatorio + eliminar vértices aleatoriamente → cientos de pares desde las 197 tazas | Malla `.ply` del objeto completado | E4 espera malla; puede tener artefactos pequeños |
| **4 — STL** | Tazas_limpias 191 no-watertight *(test)*; Thingi10K *(test robustez)* | Mallas con agujeros y normales rotas → aplicar Poisson + cerrar + reparar normales | Fichero `.stl` watertight válido para laminador | E5 solo necesita el `.stl` |
| **5 — App** | — | Código (Gradio/Streamlit) que encadena E1→E2→E3→E4 | Interfaz web: subir fotos → descargar `.stl` | — |

### 7.3 La categoría de objetos: estrategia de vasijas

En lugar de ceñirse solo a tazas (`mug`), se recomienda usar la super-categoría **"vasijas/recipientes"**: `cup + mug + bowl + vase`. Tienen la misma topología (objetos huecos, boca abierta), están todas disponibles en Objaverse y en CO3D, y multiplican el volumen del dataset por 4 sin perder coherencia semántica para el modelo de IA.

| Fuente | cup | mug | bowl | vase | Total aprox. |
|--------|-----|-----|------|------|-------------|
| Objaverse (modelos 3D) | 70 | 126 | ~200 | ~300 | **~700** |
| CO3D (secuencias de fotos reales) | ✅ | — | ✅ | ✅ | 3 categorías |
| ShapeNet (cuando llegue acceso) | ✅ | 214 | 343 | ✅ | ~600+ |
| Fantastic Breaks (objetos rotos reales) | cerámica ✅ | cerámica ✅ | cerámica ✅ | cerámica ✅ | subconjunto |

Esto frente a los ~246 modelos de solo tazas supone pasar de una muestra pequeña a un dataset de entrenamiento sólido (~700 modelos en Objaverse antes de ShapeNet).

### 7.4 Nota sobre el problema sim-a-real (brecha entre renders y fotos de móvil)

El modelo de la **etapa 2** se entrena con imágenes renderizadas (sintéticas) pero en producción recibe fotos de móvil. Para reducir esta brecha:

- **Etapa 1 como "normalizador":** SAM elimina el fondo antes de que las imágenes lleguen a la etapa 2. La etapa 2 recibe siempre objetos recortados, sin importar si la foto original tenía fondo complicado.
- **Data augmentation en los renders:** añadir ruido, variación de luz y recortes imperfectos *durante el entrenamiento* de la etapa 2.
- **CO3D como validación de realismo:** se entrena con renders aumentados y se comprueba con CO3D que funciona con fotos reales.

> **Regla de interfaz clave:** el formato de salida de la etapa 1 debe ser *idéntico* al formato de entrada de los datos de entrenamiento de la etapa 2. Si la etapa 2 se entrena con imágenes recortadas sobre fondo negro de 256×256 px, la etapa 1 debe entregar exactamente eso. Este es el acuerdo más crítico del 21 de junio.

---

## 8. Bibliografía de referencia

**Reconstrucción 3D / renderizado neuronal**
- Mildenhall et al. (2020). *NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis.* ECCV.
- Kerbl et al. (2023). *3D Gaussian Splatting for Real-Time Radiance Field Rendering.* SIGGRAPH.
- Schönberger & Frahm (2016). *Structure-from-Motion Revisited* (COLMAP). CVPR.
- Wang et al. (2021). *NeuS: Learning Neural Implicit Surfaces by Volume Rendering for Multi-view Reconstruction.* NeurIPS.

**Representación e image-to-3D**
- Park et al. (2019). *DeepSDF: Learning Continuous Signed Distance Functions for Shape Representation.* CVPR.
- Mescheder et al. (2019). *Occupancy Networks: Learning 3D Reconstruction in Function Space.* CVPR.
- Liu et al. (2023). *Zero-1-to-3: Zero-shot One Image to 3D Object.* ICCV.
- Hong et al. (2024). *LRM: Large Reconstruction Model for Single Image to 3D.* ICLR.

**Completado / reparación de forma**
- Dai et al. (2017). *Shape Completion using 3D-Encoder-Predictor CNNs and Shape Synthesis.* CVPR.
- Yuan et al. (2018). *PCN: Point Completion Network.* 3DV.
- Yu et al. (2021). *PoinTr: Diverse Point Cloud Completion with Geometry-Aware Transformers.* ICCV.
- Lamb et al. (2023). *Fantastic Breaks: A Dataset of Paired 3D Scans of Real-World Broken Objects and Their Complete Counterparts.* CVPR.
- Lamb et al. (2023). *Pix2Repair: Implicit Shape Restoration from Images.*

**Datasets**
- Chang et al. (2015). *ShapeNet: An Information-Rich 3D Model Repository.* arXiv:1512.03012.
- Collins et al. (2022). *ABO: Dataset and Benchmarks for Real-World 3D Object Understanding.* CVPR.
- Deitke et al. (2023). *Objaverse: A Universe of Annotated 3D Objects.* CVPR.
- Reizenstein et al. (2021). *Common Objects in 3D (CO3D).* ICCV.
- Downs et al. (2022). *Google Scanned Objects: A High-Quality Dataset of 3D Scanned Household Items.* ICRA.
- Zhou & Jacobson (2016). *Thingi10K: A Dataset of 10,000 3D-Printing Models.* arXiv:1605.04797.

---

## 9. Recomendación final (resumen)

- **Estrategia:** **núcleo P0 primero** (etapas 2 y 3 propias; 1/4/5 con herramientas), reparto **2-2-1**, extensiones P1/P2 solo si sobra tiempo.
- **Alcance comprometido:** pipeline end-to-end sobre **una categoría de objetos acotada**.
- **Foco de innovación:** etapas **2 (reconstrucción)** y **3 (reparación)**.
- **Datasets:** ShapeNet (base/comparación) + Fantastic Breaks (roto→reparado) + CO3D/GSO (fotos reales) + Thingi10K (imprimibilidad).
- **Clave de gestión:** acordar interfaces en la semana 1, **congelar el núcleo el 16 de agosto** y blindar el tiempo de integración.
