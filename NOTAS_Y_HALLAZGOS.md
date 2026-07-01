# Notas y hallazgos del TFM — registro vivo

> Cuaderno de bitácora del proyecto: observaciones técnicas, decisiones y cosas aprendidas sobre la marcha.
> Se va actualizando con cada avance. Raquel Roca.

---

## Estructura de carpetas del proyecto (`C:\edf\tfm\`)

- **`Documentacion/`** — todas las guías y documentos generados (`.pdf` + `.md`) y el diagrama del pipeline.
  - `TFM_01_Propuesta` · `TFM_02_Guia_Completa` · `TFM_03_Guia_Blender_Herramientas` · `TFM_04_Tutorial_Practico` · `TFM_05_Guia_Descarga_Datasets` · `TFM_07_FAQ` · `TFM_Diagrama_Pipeline.png`
- **`Notebooks/`** — cuadernos de Colab/Jupyter (`TFM_06_Cuaderno_Tazas.ipynb`).
- **`Datos/`** — datasets descargados. `Datos/tazas_objaverse/` = 246 modelos de tazas (.glb, ~747 MB) de Objaverse + `metadatos_tazas.csv`, `metadatos_tazas_completo.json`, `tazas_por_categoria.json`.
- **`Scripts/`** — scripts del proyecto. `descargar_tazas.py` (descarga + metadatos) y `filtrar_normalizar_tazas.py` (limpieza).
- **`Datos/tazas_limpias/`** — 197 tazas válidas, normalizadas (.ply, ~215 MB) + `Datos/informe_filtrado.csv`.
- **`Modelos_generados/`** — salidas del pipeline (mallas, STL...).
- **`Figuras/`** — imágenes y visualizaciones para la memoria/slides.
- **`NOTAS_Y_HALLAZGOS.md`** — este documento.
- *(Carpetas originales de Raquel, no tocadas: `AlgunasIdeas/`, `ApuntesMaster/`, `BasesTFM/`, `TareaDeepLearning/`, `TEMAS TFM.pdf`.)*

---

## Hallazgos técnicos

### H1 — Los modelos de Objaverse NO son imprimibles tal cual (no watertight)
**(13 jun 2026)** Al cargar la primera taza descargada de Objaverse, tiene solo **486 vértices, 452 caras y `is_watertight = False`**. Es decir, los modelos vienen "tal cual" los subió la gente: de baja resolución y con la malla abierta.
**Implicación para el proyecto:** confirma en la práctica que la **etapa 4 (reparación de malla → watertight)** es imprescindible antes de poder imprimir. Es un argumento real para la memoria.

### H2 — La categoría `mug` de Objaverse tiene pocos modelos (126)
**(13 jun 2026)** La categoría LVIS `mug` solo tiene **126 modelos**. Para entrenar puede quedarse corto.
**Opciones para ampliar:** combinar con categorías afines (`cup`, `teacup`, `measuring_cup`); usar los **214 mugs de ShapeNet** cuando aprueben el acceso; y/o **generar roturas sintéticas** (data augmentation) para multiplicar ejemplos en la etapa 3.

### H3 — Instalación de nerfstudio en Colab: los "errores" rojos son avisos
**(12 jun 2026)** Al instalar nerfstudio con el notebook oficial, salen muchos mensajes rojos de `dependency conflicts` (protobuf, dill...). **No son errores reales**: la instalación termina con `Successfully installed ... nerfstudio-1.1.5`. Eso sí, **hay que reiniciar el entorno** ("Restart runtime") antes de usar los comandos `ns-...`.

### H6 — Dataset limpio: 197 tazas válidas, y solo 6 son watertight
**(13 jun 2026)** Tras filtrar/normalizar (`Scripts/filtrar_normalizar_tazas.py`): **197 válidas**, 49 descartadas (degeneradas, <1.000 caras), 21 simplificadas (eran >200k caras, reducidas a 200k con `fast-simplification`). Tamaño: **653 MB → 215 MB**. Todas centradas en el origen y a escala unidad.
**Hallazgo fuerte:** solo **6 de 197 tazas son watertight** → 191 NO son imprimibles tal cual. **Confirma que la etapa 4 (reparación de malla) es imprescindible**, no opcional. Argumento clave para la memoria.
**Pendiente menor:** alguna malla muy compleja no baja del todo a 200k al simplificar (la mayor quedó en ~330k); irrelevante para seguir.

### H5 — Dataset completo de tazas descargado: 246 modelos, calidad muy variable
**(13 jun 2026)** Descargadas TODAS las tazas de Objaverse (categorías mug 126 · cup 70 · Dixie_cup 20 · teacup 19 · measuring_cup 11 = **246 únicas**, ~747 MB) con `Scripts/descargar_tazas.py`, junto con metadatos completos.
**Observaciones:** la **resolución varía muchísimo** (de 352 caras a >500.000 caras por modelo) → habrá que **filtrar/normalizar** (descartar los degenerados y quizá simplificar los enormes). Casi todas tienen licencia **CC-BY** (`by`) → uso permitido citando al autor (apuntar en la memoria).
**Implicación:** el `metadatos_tazas.csv` permite **seleccionar un subconjunto de calidad homogénea** para entrenar, en vez de usar las 246 a ciegas.

### H4 — El cuaderno de tazas funciona en local (Python 3.14) y en Colab
**(13 jun 2026)** Probado de principio a fin en la máquina de Raquel: `objaverse 0.1.7`, `trimesh 4.12.2`, `matplotlib 3.11.0` instalan y funcionan en **Python 3.14.4**. Se blindó la celda de descarga (`google.colab`) con try/except para que **también funcione en VS Code**.
**Nota:** por defecto Objaverse descarga a la caché del usuario (`~/.objaverse`); para el TFM se copian los modelos a `Datos/tazas_objaverse/` dentro del proyecto.

---

## Decisiones tomadas

- **Categoría inicial:** TAZAS (mugs/cups). Revisable. Permite roturas reales (Fantastic Breaks) y fotos reales (CO3D `cup`).
- **Estrategia:** núcleo P0 primero (etapas 2+3 con IA; 1/4/5 con herramientas), reparto 2-2-1.
- **Datasets:** stack abierto (Objaverse + Fantastic Breaks + CO3D + Thingi10K); ShapeNet solicitado pero NO imprescindible.

---

### H7 — Estrategia de dataset: ampliar de "tazas" a "vasijas"
**(16 jun 2026)** Analizado el volumen de datos disponible por categoría. Solo tazas (cup+mug) = ~246 modelos. Ampliando a la super-categoría **vasijas** (cup+mug+bowl+vase), todas con la misma topología (huecas, boca abierta):
- Objaverse: ~700 modelos totales (vs 246 actuales).
- CO3D: cubre cup, bowl y vase con fotos reales.
- ModelNet40: 163 modelos ya watertight de cup+bowl → ideal para E3.
- ShapeNet (pendiente): añadiría ~600 más.
**Implicación:** ampliar `descargar_tazas.py` para incluir bowl y vase en Objaverse. CO3D se descarga con `Scripts/descargar_co3d.py` (nuevo).

### H8 — El interface E1→E2 es el acuerdo más crítico del 21 jun
**(16 jun 2026)** La etapa 1 debe producir exactamente el formato que la etapa 2 espera para entrenamiento. Si E2 entrena con imágenes 256×256 recortadas sobre fondo negro, E1 debe entregar exactamente eso. Sin este acuerdo la integración falla aunque cada módulo funcione por separado.

---

## Pendientes / siguientes pasos

- [x] Descargar el dataset completo de tazas de Objaverse + metadatos (246 modelos). **(13 jun)**
- [x] **Filtrar/normalizar el dataset**: 197 válidas, normalizadas, en `Datos/tazas_limpias/`. **(13 jun)**
- [x] Decidir estrategia de dataset: super-categoría vasijas (cup+mug+bowl+vase). **(16 jun)**
- [ ] **Jueves 18 jun** — Presentar el tema al grupo/tutor con `TFM_01_Propuesta.md` actualizado.
- [ ] **21 jun** — Cerrar interfaces entre etapas (formato E1→E2 y E2→E3 especialmente).
- [ ] Ampliar `descargar_tazas.py` para incluir `bowl` y `vase` de Objaverse (~500 modelos extra).
- [ ] Descargar CO3D: `python Scripts/descargar_co3d.py` (cup+bowl+vase, ~8 GB).
- [ ] Descargar ModelNet40 cup+bowl (163 modelos watertight para E3).
- [ ] Decidir método de reconstrucción para E2 (nerfacto vs image-to-3D feed-forward como Zero123).
- [ ] Cuando aprueben ShapeNet, descargar synsets: mug `03797390`, bowl `02880940`, jar `03593526`.

### H9 — ShapeNet: acceso aprobado, pero la web no funciona → usar mirror de Hugging Face
**(26 jun 2026)** Raquel consiguió acceso a shapenet.org pero la web no carga (login/visor rotos, problema conocido). Solución: el acceso ahí solo sirve para aceptar términos; los datos reales se navegan/descargan desde el **mirror oficial de HF** `ShapeNet/ShapeNetCore` (gated: aceptar términos + token de HF). Creado `Scripts/inspeccionar_shapenet.py` para bajar solo `taxonomy.json`, listar categorías + nº de modelos, y opcionalmente bajar solo los synsets de vasijas (no los 51K). Conteos exactos por categoría: sacarlos del taxonomy.json (no fiados de memoria).

### H10 — Organización del grupo: GitHub + propiedad primario/secundario
**(26 jun 2026)** El grupo (5 personas) quiere "tocar todo". Acordado modelo: (1) arranque común con pipeline de juguete, (2) matriz de propiedad primario+secundario (cada persona toca 2 etapas), (3) GitHub con PR revisados + contratos de interfaz + datos fuera de Git. Aún NO tienen repo (irán a GitHub). Generados 3 docs nuevos: `TFM_09_Organizacion_Grupo`, `TFM_10_Guia_Git_Grupo`, `TFM_11_Contratos_Interfaz` (este último recoge el hito crítico de interfaces, pendiente desde el 21 jun).

## Pendientes nuevos (26 jun)
- [ ] Probar `Scripts/inspeccionar_shapenet.py` con token de HF (aceptar términos en la web del dataset primero).
- [ ] Reunión de reparto: rellenar la matriz de propiedad de `TFM_09`.
- [ ] Crear el repo de GitHub `tfm-reconstruccion-3d` (privado) e invitar a los 5; subir `.gitignore` de `TFM_10`.
- [ ] Cerrar las decisiones pendientes de `TFM_11` (resolución imagen, método E2 con/sin poses, representación E2→E3).
