# TFM — Documento de referencia completo
> Raquel Roca · Junio 2026 · Entrega: 15 sep 2026 · Grupo de 5 personas
> Consolida la propuesta, los hallazgos técnicos y las preguntas frecuentes en un solo lugar.

---

## 1. La idea

Una aplicación que, a partir de **varias fotos de un objeto**, reconstruye su modelo 3D, **rellena con IA las partes dañadas o que faltan**, y genera un archivo **STL listo para imprimir** en una impresora 3D.

El elemento diferenciador frente a un escáner 3D normal es la **reparación automática de las partes dañadas**. Caso de uso concreto: se te rompe una pieza de cerámica (una taza, un cuenco, un jarrón), la fotografías, la reconstruyes y la reimprimes.

**Flujo en una línea:**
```
Fotos de móvil → Reconstrucción 3D → Reparación IA → STL imprimible
```

---

## 2. El pipeline: 5 etapas

| # | Etapa | Qué hace | ¿Es IA propia? | Herramientas |
|---|-------|----------|----------------|-------------|
| 1 | **Captura y preprocesado** | Segmenta el objeto del fondo, estima las poses de cámara | No (herramientas existentes) | SAM + COLMAP |
| **2** | **Reconstrucción 3D** | De imágenes a nube de puntos / malla | **Sí — núcleo IA** | NeRF / Gaussian Splatting / image-to-3D |
| **3** | **Reparación / completado** | Rellena las partes dañadas o que faltan | **Sí — núcleo IA** | Shape completion (PoinTr, PCN…) |
| 4 | **Generación del STL** | Hace la malla watertight e imprimible | No (herramientas existentes) | Open3D / MeshLab |
| 5 | **App end-to-end** | Interfaz para subir fotos y descargar el STL | No | Gradio / Streamlit |

**Las etapas 2 y 3 son el TFM real.** Las demás sirven para demostrar el resultado de punta a punta.

---

## 3. Estrategia de ejecución

### 3.1 Reparto 2-2-1
- **2 personas → Etapa 2** (reconstrucción): la más grande, aguanta dos.
- **2 personas → Etapa 3** (reparación): la más novedosa e investigadora.
- **1 persona → "fontanería"**: etapas 1 + 4 + 5 con herramientas + integración del pipeline.

### 3.2 Niveles de alcance (prioridades)

| Nivel | Qué incluye | Fecha límite |
|-------|-------------|-------------|
| **P0 — Compromiso de entrega** | Pipeline end-to-end sobre vasijas (cup+mug+bowl+vase), etapas 2 y 3 propias, 1/4/5 con herramientas | **16 ago 2026** |
| **P1 — Si sobra tiempo** | Que funcione con fotos reales de móvil (no solo renders); más categorías de objetos; validar con CO3D | Sep 2026 |
| **P2 — Lujo** | App real con UI; comparativa amplia de métodos; demo en vivo | Solo si P0 y P1 van muy bien |

> Solo se compromete el **P0** en la propuesta. P1 y P2 se presentan como "trabajo futuro".

---

## 4. Datasets: estado actual y plan completo

### 4.1 Qué tenemos ya

| Dataset | Estado | Qué hay | Tamaño |
|---------|--------|---------|--------|
| **Objaverse — tazas** | ✅ Descargado | 246 modelos .glb (mug+cup+Dixie_cup+teacup+measuring_cup) | ~747 MB |
| **Tazas limpias (.ply)** | ✅ Procesado | 197 modelos normalizados, centrados, escala unidad | ~215 MB |
| **informe_filtrado.csv** | ✅ Generado | Metadatos de los 197 modelos (caras, watertight, etc.) | — |

### 4.2 Plan de descarga por etapa

| Dataset | Para qué etapa | Qué se extrae | Estado | Script |
|---------|---------------|---------------|--------|--------|
| **Objaverse** (bowl + vase) | E2 train, E3 train | ~500 modelos .glb adicionales | Pendiente | Ampliar `descargar_tazas.py` |
| **CO3D** (cup + bowl + vase) | E1 val, E2 val/train P1 | ~1.230 secuencias de fotos reales con poses | Pendiente | `Scripts/descargar_co3d.py` |
| **ModelNet40** (cup + bowl) | E3 train | 163 modelos ya watertight, ideales para pares (roto, completo) | Pendiente | Código en FAQ 6 |
| **Fantastic Breaks** | E3 validación | 150 objetos realmente rotos ↔ completos | Pendiente | Manual (web del dataset) |
| **ShapeNet** (mug+bowl+vase) | E2/E3 train extra | ~600 modelos CAD de alta calidad | Acceso solicitado | Manual tras aprobación |
| **Thingi10K** | E4 test | 10.000 STL de calidad variable | Pendiente | GitHub del dataset |

### 4.3 Por qué la super-categoría "vasijas" y no todas las categorías

Ampliar a bowl + vase **cuadruplica el dataset** (~700 modelos en Objaverse frente a 246) sin perder coherencia: todas son objetos huecos con boca abierta, misma topología, y todas están en CO3D y Fantastic Breaks.

Usar **todas las categorías** de Objaverse (800.000 objetos) no es viable:
- Descarga: ~8 TB
- Entrenamiento: meses con GPUs industriales (lo que publican grupos de investigación grandes)
- Calidad: el modelo aprendería formas tan variadas que sería peor en vasijas que uno especializado

| Fuente | cup | mug | bowl | vase | Total aprox. |
|--------|-----|-----|------|------|-------------|
| Objaverse (3D) | 70 | 126 | ~200 | ~300 | **~700** |
| CO3D (fotos reales) | ✅ | — | ✅ | ✅ | ~1.230 secuencias |
| ShapeNet (pendiente) | ✅ | 214 | 343 | ✅ | ~600+ |
| ModelNet40 (watertight) | 99 | — | 64 | — | 163 |
| Fantastic Breaks | cerámica ✅ | cerámica ✅ | cerámica ✅ | cerámica ✅ | subconjunto |

---

## 5. Flujo de datos entre etapas

Esta es la parte más importante para el acuerdo del 21 de junio. El formato de salida de cada etapa es el contrato con la siguiente.

### 5.1 Diagrama completo

```
  DATASETS DE ENTRENAMIENTO            FLUJO EN USO REAL (demo)
  ─────────────────────────            ────────────────────────

  Objaverse .glb (~700 vasijas)        Fotos del móvil (8-20 imágenes)
    │ renderizar 16-36 vistas                      │
    │ + data augmentation                          ▼
    ▼                               ┌──────────────────────────┐
  Imágenes sintéticas ──train──►   │  ETAPA 1 — Captura       │
                                   │  SAM (quita fondo)        │
  CO3D cup/bowl/vase               │  COLMAP (poses cámara)    │
    │ fotos reales                 └──────────────────────────┘
    ▼                                             │
  Validación E1+E2  ──val──►          N imágenes sin fondo (PNG)
                                      + cameras.json (poses)
                                                  │
                                                  ▼
  Objaverse .glb    ──train──►  ┌──────────────────────────┐
  (renders + poses)             │  ETAPA 2 — Reconstrucción │
                                │  NeRF / Gaussian Splatting│
  CO3D              ──val──►    │  / image-to-3D            │
                                └──────────────────────────┘
                                                  │
                                    Nube de puntos / malla
                                    del objeto ROTO (.ply)
                                    (normalizada: centrada,
                                     escala unidad)
                                                  │
                                                  ▼
  Objaverse .ply    ──train──►  ┌──────────────────────────┐
  (rotura sintética)            │  ETAPA 3 — Reparación    │
  ModelNet40        ──train──►  │  Shape completion (DL)    │
  Fantastic Breaks  ──val──►    └──────────────────────────┘
                                                  │
                                    Malla 3D COMPLETA (.ply)
                                                  │
                                                  ▼
  Tazas_limpias 191 ──test──►  ┌──────────────────────────┐
  Thingi10K         ──test──►  │  ETAPA 4 — STL           │
                               │  Open3D / MeshLab         │
                               └──────────────────────────┘
                                                  │
                                            .STL válido
                                                  │
                                                  ▼
                                           Impresora 3D
```

### 5.2 Tabla de interfaces (contratos entre etapas)

| Etapa | Qué recibe | Qué produce | Formato exacto (a acordar el 21 jun) |
|-------|-----------|-------------|--------------------------------------|
| **E1** | Fotos móvil (JPEG/PNG) | Imágenes recortadas + poses | N PNGs sin fondo + `cameras.json` (intrínsecas + extrínsecas) |
| **E2** | Salida de E1 | Modelo 3D del objeto roto | `.ply` nube de puntos normalizada (centrada, escala unidad) |
| **E3** | Salida de E2 | Modelo 3D completo | `.ply` malla completa |
| **E4** | Salida de E3 | STL imprimible | `.stl` watertight |

### 5.3 El problema sim-to-real y cómo se resuelve

**El problema:** si la etapa 2 entrena con renders perfectos (fondo blanco, luz ideal) pero en producción recibe fotos de móvil (fondo real, sombras, blur), el modelo fallará.

**La solución, en capas:**

1. **Etapa 1 como normalizador:** SAM elimina el fondo antes de que las imágenes lleguen a E2. E2 recibe siempre el objeto recortado, sin importar el fondo original. Esto reduce mucho la brecha.
2. **Data augmentation en los renders:** durante el entrenamiento de E2, se añaden fondos aleatorios, ruido y variación de luz a los renders sintéticos para que el modelo no dependa de condiciones perfectas.
3. **CO3D como validación de realismo (P0) y training real (P1):** se comprueba que el modelo entrenado con renders funciona con las fotos reales de CO3D; si no, se añade CO3D al training.

> **Regla de interfaz crítica:** el formato que produce E1 debe ser idéntico al formato de los datos con que E2 fue entrenada. Este es el acuerdo más importante del 21 de junio.

---

## 6. Hallazgos técnicos probados

Estos son hechos comprobados empíricamente, no suposiciones. Son el argumento más fuerte para presentar el tema.

### H1 — Los modelos de Objaverse NO son imprimibles tal cual
*(13 jun)* La primera taza cargada: 486 vértices, 452 caras, `is_watertight = False`. Los modelos de Objaverse son assets de visualización, no de impresión 3D. **Prueba empírica de que la etapa 4 existe y es necesaria.**

### H6 — Solo 6 de 197 tazas son watertight
*(13 jun)* Después de filtrar y normalizar 246 modelos: 197 válidos, y de esos **solo 6 son directamente imprimibles**. Los otros 191 tienen agujeros o normales rotas. **Esto no es un problema teórico — es el dataset real del proyecto y justifica toda la etapa 4.**

### H5 — Dataset completo descargado: 246 modelos, calidad muy variable
*(13 jun)* Descargadas las 5 categorías de tazas de Objaverse (mug 126, cup 70, Dixie_cup 20, teacup 19, measuring_cup 11). Resolución varía de 352 a 500.000+ caras por modelo. Casi todas bajo licencia CC-BY (uso libre citando al autor).

### H2 — La categoría mug sola tiene pocos modelos (126)
*(13 jun)* Para entrenar una red neuronal de reconstrucción o reparación, 126 modelos es escaso. Solución: expandir a vasijas (cup+mug+bowl+vase, ~700 en Objaverse) y generar variantes sintéticas mediante data augmentation.

### H4 — El entorno funciona: Python 3.14 local y Google Colab
*(13 jun)* El cuaderno `TFM_06_Cuaderno_Tazas.ipynb` funciona en ambos entornos. Las librerías clave (`objaverse 0.1.7`, `trimesh 4.12.2`, `matplotlib 3.11.0`) instaladas y probadas.

### H3 — Nerfstudio en Colab: los errores rojos son avisos, no errores
*(12 jun)* Al instalar nerfstudio salen mensajes rojos de conflictos de dependencias. No son errores reales — la instalación termina con `Successfully installed nerfstudio-1.1.5`. Hay que reiniciar el entorno después.

### H7 — Estrategia de dataset: vasijas multiplica por ~4 el volumen
*(16 jun)* Ampliando de "tazas" a "vasijas" (cup+mug+bowl+vase): ~700 modelos en Objaverse, CO3D cubre las 3 categorías principales con fotos reales, ModelNet40 aporta 163 modelos ya watertight. Coherencia semántica mantenida (todos son recipientes huecos).

### H8 — La interfaz E1→E2 es el riesgo de integración más alto
*(16 jun)* Si E2 se entrena con imágenes de un formato/resolución y E1 entrega otro, el pipeline entero falla aunque cada módulo funcione por separado. Este acuerdo tiene que estar cerrado antes del 21 de junio.

---

## 7. Preguntas frecuentes (respuestas clave)

### ¿Para qué sirven las imágenes que se generan a partir de los modelos 3D?

Para entrenar la reconstrucción (etapa 2). La red aprende el mapeo *imágenes → forma 3D* y para eso necesita pares con solución conocida. Al "fotografiar" virtualmente los modelos `.glb` desde varios ángulos, fabricamos esos pares automáticamente: la imagen es el ejercicio, el `.glb` es la solución correcta.

### ¿Las imágenes de entrenamiento deben tener fondo o no?

Depende del acuerdo de interfaz con la etapa 1:
- Si E1 entrega imágenes **sin fondo** → E2 se entrena con renders sin fondo. E1 se vuelve crítica (el recorte debe ser bueno).
- Si E1 entrega imágenes **con fondo** → E2 se entrena con renders aumentados (fondos aleatorios). E2 es más robusta pero más difícil de entrenar.

La opción recomendada para P0: entrenar E2 con imágenes sin fondo, y que E1 entregue siempre imágenes con el fondo eliminado por SAM.

### ¿No es mejor usar fotos reales directamente para entrenar E2?

Sí, y eso es CO3D. Pero para P0 se usa Objaverse con renders porque:
1. Tienes las poses de cámara perfectas (gratis, sin calibración).
2. Tienes el ground truth 3D exacto.
3. Puedes generar miles de pares sin depender de cuántos objetos haya fotografiados en CO3D.

CO3D en P0 es **validación** ("¿funciona con fotos reales?"). En P1 pasa a ser también **training**.

### ¿Qué hace falta para entrenar la etapa 3 (reparación)?

Pares de (modelo roto, modelo completo). Se generan sintéticamente a partir de los 197 modelos limpios: se corta con un plano aleatorio, se eliminan vértices aleatoriamente, etc. Con 197 modelos y varias roturas por modelo, se pueden generar cientos de pares de entrenamiento. Fantastic Breaks aporta roturas reales (más difíciles) para validación.

### ¿Por qué solo vasijas y no todos los objetos?

Porque entrenar sobre todas las categorías de Objaverse (800.000 objetos) requiere terabytes de descarga y meses de GPU. Un modelo especializado en vasijas da mejor calidad en vasijas que un modelo generalista, con una fracción del coste. "Más categorías" es extensión P1, no objetivo P0.

---

## 8. Cronograma y hitos críticos

| Fase | Fechas | Hito |
|------|--------|------|
| **Arranque** | 10–21 jun | Datasets descargados; interfaces entre etapas acordadas; repo y entorno comunes |
| **Desarrollo en paralelo** | 22 jun – 2 ago | E2 y E3 propias; E1/E4/E5 con herramientas. Demo por módulo ~17 jul |
| **Integración P0** | 3–16 ago | **Pipeline completo foto → STL funcionando** |
| **Evaluación** | 17–30 ago | Métricas (Chamfer, IoU, imprimibilidad); extensiones P1 si P0 está sólido |
| **Redacción** | 31 ago – 12 sep | Memoria final + slides |
| **Entrega** | 15 sep | — |

**Hitos con fecha inamovible:**
- **18 jun (mañana)** — Presentar tema al grupo/tutor
- **21 jun** — Interfaces entre etapas acordadas (sin esto, la integración de agosto fracasa)
- **16 ago** — Núcleo P0 congelado
- **15 sep** — Entrega

⚠️ **Riesgo agosto:** la integración (la fase más delicada) cae en el mes de vacaciones. Pactar disponibilidad o adelantar lo posible a julio.

---

## 9. Estado actual y pendientes

### Ya hecho
- [x] 246 modelos .glb de vasijas/tazas descargados de Objaverse (~747 MB)
- [x] 197 modelos limpios y normalizados (.ply, ~215 MB) en `Datos/tazas_limpias/`
- [x] Hallazgo clave documentado: solo 6/197 son watertight → argumento para la memoria
- [x] Cuaderno `TFM_06_Cuaderno_Tazas.ipynb` probado en local y en Colab
- [x] Nerfstudio instalado y probado en Colab
- [x] Decisión de estrategia de dataset: super-categoría vasijas
- [x] `Scripts/descargar_co3d.py` creado (listo para ejecutar)

### Pendiente urgente (antes del 21 jun)

| Tarea | Por qué es urgente | Cómo |
|-------|--------------------|------|
| Ampliar Objaverse a bowl + vase | Triplicar el dataset de E2/E3 | Editar `descargar_tazas.py`, añadir `"bowl"` y `"vase"` |
| Descargar CO3D cup+bowl+vase | Datos reales para validar E1 y E2 | `python Scripts/descargar_co3d.py` (~8 GB) |
| Descargar ModelNet40 cup+bowl | 163 modelos watertight para E3 | Código en FAQ 6 del TFM_07 |
| Acordar interfaz E1→E2 y E2→E3 | Sin esto no hay integración | Reunión del grupo |
| Solicitar ShapeNet si no se ha hecho | Acceso tarda días | Formulario en shapenet.org |

### Pendiente no urgente
- Decidir método de reconstrucción para E2: nerfacto (NeRF) vs Zero123/LRM (image-to-3D feed-forward)
- Cuando llegue acceso ShapeNet: synsets mug `03797390`, bowl `02880940`, vase `03593526`
- Descargar Fantastic Breaks (web del dataset)
- Descargar Thingi10K (GitHub del dataset)

---

## 10. Estructura de ficheros del proyecto

```
C:\EDF\TFM\
├── Documentacion\
│   ├── TFM_00_Referencia_Completa.md   ← este documento
│   ├── TFM_01_Propuesta.md             ← propuesta completa para el grupo
│   ├── TFM_02_Guia_Completa.md         ← manual educativo de conceptos 3D y DL
│   ├── TFM_03_Guia_Blender_Herramientas.md
│   ├── TFM_04_Tutorial_Practico.md     ← código ejecutable en Colab
│   ├── TFM_05_Guia_Descarga_Datasets.md
│   ├── TFM_07_FAQ.md                   ← preguntas frecuentes (documento vivo)
│   └── TFM_Diagrama_Pipeline.png
├── Notebooks\
│   └── TFM_06_Cuaderno_Tazas.ipynb    ← descarga + carga + visualiza + STL
├── Scripts\
│   ├── descargar_tazas.py              ← descarga Objaverse (ampliar a bowl+vase)
│   ├── filtrar_normalizar_tazas.py     ← limpieza → 197 modelos válidos
│   └── descargar_co3d.py              ← descarga CO3D cup+bowl+vase (pendiente)
├── Datos\
│   ├── tazas_objaverse\               ← 246 .glb originales (~747 MB)
│   ├── tazas_limpias\                 ← 197 .ply normalizados (~215 MB)
│   ├── informe_filtrado.csv
│   ├── metadatos_tazas.csv
│   └── metadatos_tazas_completo.json
├── Modelos_generados\                 ← salidas del pipeline (taza_0.stl de demo)
├── Figuras\                           ← visualizaciones (taza_0_nube.png)
└── NOTAS_Y_HALLAZGOS.md              ← bitácora técnica viva
```
