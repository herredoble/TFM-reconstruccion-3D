# Notas y hallazgos del TFM — registro vivo

> Bitácora del proyecto: decisiones, hallazgos técnicos y estado actual.
> Raquel Roca · se actualiza con cada avance.

---

## Decisiones tomadas

### D1 — Categoría: vasijas ampliadas (mug + bowl + bottle + jar + can)
*(16 jun 2026 · ampliado jul 2026)*
La categoría inicial era solo "tazas" (mug). Ampliado progresivamente a la super-categoría **vasijas** por topología compartida (objetos huecos, cilíndricos o con boca abierta) y cobertura cruzada en todos los datasets:

| Synset | Categoría | ShapeNet | Razón de inclusión |
|--------|-----------|----------|--------------------|
| 03797390 | mug (taza) | ~214 | Categoría original |
| 02880940 | bowl (cuenco) | ~343 | Misma topología, en CO3D y Fantastic Breaks |
| 02876657 | bottle (botella) | ~498 | Cilíndrica, se rompe igual, mayor volumen |
| 03593526 | jar (tarro) | ~172 | Topología idéntica al mug |
| 02946921 | **can (lata)** | ~108 | Cilíndrica, se rompe/abolla de forma realista; puente natural hacia lo industrial (industria alimentaria, control de calidad de envases) sin añadir complejidad arquitectónica |
| 03991062 | flowerpot (maceta) | ~164 | Opcional — misma topología cilíndrica, fácil de añadir |

**P0 usa:** mug + bowl + bottle + jar + can (~1.335 modelos ShapeNet). Flowerpot queda como extensión fácil si conviene más volumen.

CO3D y Fantastic Breaks cubren estas mismas categorías con datos reales.

### D2 — Estructura de alcance: P0 / P1 / Trabajo futuro
Un núcleo sólido bien ejecutado + consciencia de las limitaciones + visión de hacia dónde va el trabajo es más creíble que abarcar todo y llegar a medias.

**P0 — Entrega obligatoria**
Pipeline end-to-end sobre vasijas (mug + bowl + bottle + jar + can). Etapas 2 y 3 con modelos propios; etapas 1/4/5 con herramientas existentes (SAM+COLMAP, Open3D/MeshLab). Resultado demostrable: foto de vasija rota → STL reparado. Reparto 2-2-1.

**P1 — Si da tiempo**
Generalizar a más categorías ShapeNet (helmet, faucet…) sin cambiar la arquitectura, solo los datos. No requiere rediseño.

**Trabajo futuro (sección de la memoria)**
- Aplicación industrial con ABC Dataset (piezas CAD, engranajes, brackets)
- Generación sintética de roturas industriales
- Integración con sistemas de inspección (visión industrial)

### D3 — Stack de datasets (abierto, sin depender de ShapeNet)
| Dataset | Para qué | Tamaño | Prioridad | Estado |
|---------|----------|--------|-----------|--------|
| ShapeNet (mug+bowl+bottle+jar+can) | E2+E3 train principal | — | — | ✅ 2.547 raw → **2.170 limpios** en `Datos/shapenet/limpias/` |
| Objaverse (mug+cup+teacup…) | E2+E3 train complementario | — | — | ✅ 246 raw → **197 limpios** en `Datos/objaverse/limpias/` |
| **Fantastic Breaks** | E3: pares roto→completo (único dataset así) | ~2 GB | Alta | ✅ 150 pares en `Datos/fantastic_breaks/` (carpetas 00/…149/) |
| CO3D (cup+bowl+vase) | E1+E2: validar que el sistema funciona con fotos reales (no entra en E3) | ~56 GB solo cup; 150+ GB cup+bowl+vase | **Baja — descargar solo cuando el pipeline funcione en sintético** | Pospuesto a fase P1. Subset de prueba: `python Scripts/descargar_co3d.py --solo cup --single_sequence_subset` |
| ModelNet40 (cup+bowl) | E3: 163 modelos watertight listos para pares roto/completo | ~500 MB | Media | Pendiente |
| Thingi10K | E4: validar imprimibilidad | ~3 GB | Baja — puede esperar a tener el pipeline funcionando | Pendiente |

ShapeNet es complemento, no bloqueante.

### D4 — Interfaz E1→E2: PNG sin fondo + cameras.json
*(acordar en reunión del 21 jun)*
E2 entrenará con renders del objeto recortado (sin fondo). E1 debe entregar exactamente el mismo formato que E2 vio en training: N PNGs sin fondo + `cameras.json` con intrínsecas y extrínsecas. Sin este acuerdo cerrado, la integración de agosto falla aunque cada módulo funcione por separado.

### D5 — Organización del grupo: arranque común + matriz de propiedad
*(26 jun 2026)*
5 personas. Modelo acordado: (1) arranque común con pipeline de juguete para que todos entiendan el flujo, (2) matriz primario/secundario (cada persona propietaria de 2 etapas), (3) GitHub privado con PR revisados, (4) datos fuera de Git (solo scripts y código en repo).

### D1-nota — El ángulo industrial
La lata (can) ya actúa como puente natural hacia lo industrial dentro de P0: misma arquitectura, mismos datos, pero con aplicación directa en industria alimentaria y control de calidad de envases.

Para ir más allá (piezas mecánicas, componentes CAD) el referente es el **ABC Dataset** (1M de modelos CAD de Onshape: engranajes, brackets, carcasas). Eso es **trabajo futuro en la memoria**, no objetivo del TFM. Documentado aquí para no perder la idea y poder argumentarlo con solidez en la defensa.

### D7 — Reparto definitivo del equipo
*(jul 2026)*
E2 (reconstrucción): **Álvaro** (arquitectura/decisión), **Almu** (implementación E1+E2), **Luis** (métricas + integración E2→E3).
E3 (reparación): **Raquel** (datos y preprocesado), **Rocío** (arquitectura del modelo).

### D8 — Método E2: Pix2Vox elegido
*(25 jul 2026 — Álvaro)*
**Pix2Vox**: reconstrucción 3D multi-vista basada en voxels. Descartados nerfacto y Zero123.

Configuración usada:
- Formato datos: `.binvox` (voxelización de todos los modelos de todas las categorías)
- Imágenes: 20 vistas por objeto, mismos ángulos fijos para todos los modelos
- Carpetas: `Datos_E2/Datos_E2_voxel` (voxels) · `Datos_E2/IMG E2` (imágenes)

**Impacto en el contrato E2→E3:** la salida de E2 es ahora un voxel grid, no una nube de puntos `.npy`. Hay que definir la conversión voxel → nube de puntos (marching cubes + muestreo, o directamente de la malla voxelizada). Luis coordina. Ver `Documentacion/TFM_11_Contratos_Interfaz.md` para actualizar el contrato.

### D6 — ShapeNet: usar mirror de Hugging Face
*(26 jun 2026)*
El acceso a shapenet.org está aprobado pero la web no carga (problema conocido). Los datos reales están en el mirror oficial `ShapeNet/ShapeNetCore` en HF (gated: aceptar términos + token HF). Script creado: `Scripts/inspeccionar_shapenet.py` para bajar solo los synsets de vasijas.

---

## Hallazgos técnicos

### H8 — ShapeNet filtrado: 2.170 modelos válidos, calidad notablemente mejor que Objaverse
*(jul 2026)*

| | ShapeNet | Objaverse |
|-|----------|-----------|
| Modelos de entrada | 2.547 | 246 |
| Válidos tras filtrar | **2.170 (85%)** | 197 (80%) |
| Simplificados (>200k caras) | 21 | 21 |
| Descartados | 377 | 49 |
| Errores | 0 | 0 |

**Dataset combinado actual: 2.170 + 197 = 2.367 modelos .ply listos para entrenar.**

ShapeNet tiene mejor tasa de calidad que Objaverse (85% vs 80%) y volumen muy superior. Pendiente: contar cuántos de los 2.170 de ShapeNet son watertight (comparar con los 6/197 de Objaverse — se espera que sean muchos más, dado que ShapeNet son modelos CAD).

**Fantastic Breaks (150 pares):** cada carpeta numerada (00/…149/) contiene `model_c.ply` (completo, ground truth E3) · `model_b_0.ply` (roto, entrada al pipeline) · `model_r_0.ply` (fragmento, proxy sintético) · `meta_0.npz` (clase, material, tipo de fractura). Es el único dataset con pares reales roto↔completo. Ver H9 para detalle completo.

### H10 — CO3D no son modelos 3D: son fotos reales con poses de cámara
*(jul 2026)*

CO3D (Meta) contiene **secuencias de vídeo/fotos** de objetos reales desde múltiples ángulos, con las poses de cámara ya calculadas. Cada secuencia es un objeto físico real fotografiado ~50-200 veces:

```
cup/secuencia_001/
├── frame_000001.jpg   ← foto de una taza desde un ángulo
├── frame_000002.jpg   ← misma taza, 5° girada
├── ...
└── cameras.json       ← posición exacta de la cámara en cada foto
```

Entra en **E1 y E2** (reconstrucción a partir de fotos reales), no en E3. El tamaño real es ~56 GB solo para `cup`, 150+ GB para `cup+bowl+vase` (20 zips en paralelo de ~18 GB cada uno — muy por encima de la estimación inicial de 8 GB).

**Cuándo descargarlo:** cuando el pipeline funcione en sintético y se quiera demostrar con fotos reales (fase P1). No es necesario para desarrollar ni validar E3, que es el núcleo del TFM.

### H9 — Fantastic Breaks: estructura real y uso en E3
*(jul 2026)*

**Qué es:** el único dataset público con objetos físicamente rotos emparejados con su versión completa. Son escaneos 3D reales — no sintéticos. Imprescindible para entrenar E3 porque ShapeNet y Objaverse solo tienen modelos completos; para reparación necesitas pares (roto → completo).

**Estructura de cada carpeta (00/ … 149/):**

| Fichero | Qué es | Uso en el TFM |
|---------|--------|---------------|
| `model_c.ply` | Objeto completo escaneado | Target de E3 — lo que queremos predecir |
| `model_b_0.ply` | Objeto roto (denso, ~1.2M puntos) | Entrada al pipeline de reparación |
| `model_r_0.ply` | Fragmento que falta (proxy sintético) | Supervisión adicional para E3 |
| `meta_0.npz` | Máscara de fractura + transformación 4×4 | Indica exactamente qué puntos son borde de rotura — anotación única, ningún otro dataset tiene esto |

**Clases y relevancia para vasijas:**

| Clase | Objetos | Relevancia |
|-------|---------|------------|
| 00 — mug | 30 | Directo |
| 02 — bowl | ~17 | Directo |
| 03 — cup | 6 | Directo |
| 05 — jar | 8 | Directo |
| **Total vasijas** | **~61** | |
| 01 — plate | 35 | Útil para shape completion aunque no es vasija |
| Resto (estatuas, misc…) | 54 | Usar con cautela |

De 150 pares totales, **~61 son vasijas directamente usables** para entrenar E3.

**Detalle técnico crítico para el preprocesado de E3:** los .ply son muy densos (~1.2M puntos). Antes de entrenar habrá que hacer **submuestreo** a 2.048 o 8.192 puntos, que es el estándar en los papers de shape completion (PoinTr, PCN…). Esto irá en el script de preprocesado de E3.

### H7 — Comparativa honesta de datasets
*(jul 2026)*

| Dataset | Calidad mallas | Volumen | Uso en papers | Para el TFM |
|---------|---------------|---------|---------------|-------------|
| **ShapeNet** | Alta (limpias, normalizadas) | 51K / 55 cat. | Estándar de referencia | Ideal para entrenar y comparar contra el estado del arte |
| **Objaverse** | Muy variable (user-upload) | 800K | Moderno pero ruidoso | Bueno para variedad; ya vimos que solo 6/197 eran watertight |
| **Fantastic Breaks** | Alta (escaneados reales) | 150 objetos | Único en su tipo | El mejor para la tarea roto→completo emparejado |
| **CO3D** | N/A (fotos, no mallas) | 1.5M frames | Meta, muy citado | Único para validar con fotos reales |
| **Thingi10K** | Real (impresión 3D real) | 10K | Para printing | Para validar imprimibilidad |

**Conclusión:** ShapeNet es mejor que Objaverse para entrenamiento porque las mallas son consistentes y limpias y los papers de ML comparan resultados sobre él. Objaverse añade variedad pero con más ruido. Combinación óptima: ShapeNet (calidad) + Objaverse (volumen) + Fantastic Breaks (roturas reales) + CO3D (validación real).

### H1 — Los modelos de Objaverse NO son imprimibles tal cual
*(13 jun 2026)* Primera taza cargada: 486 vértices, 452 caras, `is_watertight = False`. Son assets de visualización, no de impresión. **Prueba empírica de que la etapa 4 es necesaria.**

### H6 — Solo 6 de 197 tazas son watertight
*(13 jun 2026)* Tras filtrar y normalizar 246 modelos → 197 válidos. De esos, **solo 6 son directamente imprimibles**. Los otros 191 tienen agujeros o normales rotas. Argumento fuerte para la memoria: la reparación no es opcional.

### H5 — 246 modelos descargados, calidad muy variable
*(13 jun 2026)* Categorías: mug 126 · cup 70 · Dixie_cup 20 · teacup 19 · measuring_cup 11. Resolución varía de 352 a 500.000+ caras. Licencia mayoritaria CC-BY (uso libre citando autor).

### H2 — 126 mugs no son suficientes para entrenar
*(13 jun 2026)* Para una red neuronal de reconstrucción o reparación, 126 ejemplos es escaso. Solución: vasijas (~700 en Objaverse) + data augmentation (roturas sintéticas).

### H3 — Nerfstudio en Colab: los mensajes rojos son avisos, no errores
*(12 jun 2026)* Al instalar nerfstudio salen conflictos de dependencias en rojo. No son errores: la instalación termina con `Successfully installed nerfstudio-1.1.5`. Hay que reiniciar el entorno después.

### H4 — Entorno funciona en Python 3.14 local y en Colab
*(13 jun 2026)* `objaverse 0.1.7`, `trimesh 4.12.2`, `matplotlib 3.11.0` instalados y probados. Celda de descarga blindada con try/except para funcionar en ambos entornos.

---

## Estado y pendientes

### H11 — Fantastic Breaks: mapping completo de clases y corrección 03/05
*(11 jul 2026)*

Mapping real verificado contra conteos del paper (Lamb et al., CVPR 2023, Tabla 1).
El README del GitHub y el ZIP no incluyen ningún fichero de documentación con el mapping.

| Carpeta | Nombre   | Pares | Grupo TFM   |
|---------|----------|-------|-------------|
| 00      | mug      |  30   | vasija ✅   |
| 01      | plate    |  35   | plato (opcional) |
| 02      | bowl     |  17   | vasija ✅   |
| **03**  | **jar**  |   6   | vasija ✅ ← **CORRECCION: antes llamado cup** |
| **05**  | **cup**  |   8   | vasija ✅ ← **CORRECCION: antes llamado jar** |
| 06      | misc     |   2   | descartar   |
| 07      | box/misc |   3   | descartar   |
| 09      | statue   |  30   | opcional (augmentation) |
| 10      | misc     |   1   | descartar   |
| 12      | coaster  |   6   | descartar   |
| 13      | misc     |   1   | descartar   |
| 14      | misc     |   3   | descartar   |
| 17      | misc     |   1   | descartar   |
| 18      | misc     |   4   | descartar   |
| 19      | box/misc |   3   | descartar   |

**Plate (01, 35 pares) y statue (09, 30 pares) son las candidatas opcionales** si se necesita
más volumen de entrenamiento. Plate comparte topología plana (rompe diferente a vasija).
Statue añade variedad geométrica extrema. Ambas se activan con `--clases vasijas,plate,statue`.

### H12 — Dataset sintético de roturas: 2.367 pares generados
*(3 ago 2026 — Raquel)*

Generados 2.367 pares sintéticos (roto, completo) a partir de ShapeNet (2.170 modelos) + Objaverse (197 modelos).
Técnica: corte por plano aleatorio, eliminando entre 25% y 75% de puntos por par.
Resultado: 4.602 archivos .npy, 113.7 MB → `Datos/sintetico/roturas/`
Script: `Scripts/generar_roturas_sinteticas.py`
0 errores en 2.367 modelos.

**Impacto para E3:** Rocío pasa de tener 61 pares reales (Fantastic Breaks) a **2.428 pares en total**
(2.367 sintéticos + 61 reales). Los sintéticos y los reales están en carpetas separadas para poder
entrenar con cada conjunto por separado o combinados.

| Fuente | Pares | Tipo | Carpeta |
|--------|-------|------|---------|
| Fantastic Breaks | 61 | Reales (escaneos) | `Datos/fantastic_breaks/procesado/` |
| ShapeNet + Objaverse | 2.367 | Sintéticos (corte plano) | `Datos/sintetico/roturas/` |
| **Total** | **2.428** | | |

---

### H13 — E3/dataset.py: data loader PyTorch listo y probado
*(4 ago 2026 — Raquel)*

Creado `E3/dataset.py` con tres componentes:
- `construir_pares(carpetas)` — escanea directorios buscando pares `*_completo.npy` / `*_roto.npy`
- `ShapeCompletionDataset` — clase `torch.utils.data.Dataset`; augmentación: rotación aleatoria en Z + jitter σ=0.01
- `construir_dataloaders(carpetas, batch_size, split, augmentar)` — devuelve (train_loader, val_loader, test_loader)

Probado en local. Resultado del test:
- 2.362 pares encontrados (Fantastic Breaks + sintéticos)
- Split 80/10/10 → train 1.889 / val 236 / test 237
- Batch shape: `torch.Size([32, 2048, 3])`, dtype float32 ✓
- 60 batches por época en train

**Siguiente paso inmediato:** `E3/train.py` — script de entrenamiento con modelo PCN,
pérdida Chamfer Distance y bucle de entrenamiento con checkpoints.

---

### H14 — PCN baseline entrenado: val loss 0.1193 en 100 épocas
*(5 ago 2026 — Raquel)*

Primer entrenamiento completo del modelo PCN en Google Colab (T4 GPU).

**Configuración:**
- Datos: 2.362 pares (61 Fantastic Breaks reales + 2.301 sintéticos ShapeNet/Objaverse)
- Split: 1.889 train / 236 val / 237 test
- Batch size: 64, épocas: 100, LR inicial: 1e-4, StepLR ×0.5 cada 40 épocas
- Duración: ~55 minutos en T4 GPU

**Resultados:**
| Época | Train loss | Val loss | LR |
|-------|-----------|----------|-----|
| 1 | 0.310 | 0.360 | 1e-4 |
| 40 | 0.137 | 0.138 | 5e-5 (decay) |
| 80 | 0.121 | 0.125 | 2.5e-5 (decay) |
| **97 (mejor)** | **0.118** | **0.1193** | 2.5e-5 |
| 100 | 0.117 | 0.120 | 2.5e-5 |

**Interpretación:** la pérdida es CD-L1 (distancia euclídea media al vecino más cercano, escala esfera unidad radio=1). Un valor de 0.119 significa que los puntos predichos están a ~0.12 unidades de media de los puntos reales. La diferencia train/val es mínima (~0.001) — sin overfitting.

**Checkpoint:** `Datos_E2_E3/checkpoints_pcn/best.pt` en Drive compartido (época 97).

**Siguiente paso:** `E3/evaluate.py` — cargar best.pt, pasar el test set y visualizar ejemplos.

### H16 — E3 v3: CD=0.0665, F-Score=0.024 — mejora clara sobre baseline
*(13 ago 2026 — Raquel)*

Entrenamiento desde cero con hiperparámetros corregidos en A100 GPU (~40 min).

**Configuración v3:**
- Épocas: 400 (mejor en época 347) · LR: 1e-4 · lr_decay: 100 · batch: 64 · w_coarse: 0.5

**Resultados vs baseline v1:**

| Métrica | v1 (época 97) | v3 (época 347) | Mejora |
|---------|--------------|----------------|--------|
| CD media | 0.0766 | **0.0665** | ↓ 13% |
| CD mediana | 0.0732 | **0.0628** | ↓ 14% |
| CD std | 0.0283 | **0.0217** | ↓ 23% |
| F-Score media | 0.0193 | **0.0243** | ↑ 26% |

Mejora en todas las métricas. La std más baja indica predicciones más consistentes.
El modelo aún lejos de los papers (~CD 0.005–0.020) por limitaciones del PCN y roturas sintéticas simples.

**Checkpoints en Drive:** `Datos_E2_E3/E3/Raquel/modelos/v3_pcn/best.pt`
**Resultados en Drive:** `Datos_E2_E3/E3/Raquel/resultados/v3_pcn/`
**Siguiente paso:** pasar best.pt a Rocío para que compare con PoinTr/SnowFlakeNet.

### H15 — Evaluación E3 baseline: CD=0.077, F-Score=0.019 — predicciones sin estructura
*(7 ago 2026 — Raquel)*

Evaluación del checkpoint `best.pt` (época 97) sobre el test set (237 muestras).

**Resultados:**

| Métrica | Valor | Referencia (PCN en ShapeNet) |
|---------|-------|------------------------------|
| CD-L1 media | 0.0766 | ~0.005–0.020 |
| CD-L1 mediana | 0.0732 | — |
| CD-L1 std | 0.0283 | — |
| F-Score @ τ=0.01 (media) | 0.019 | ~0.40–0.60 |

Archivos generados: `E3/resultados/metricas.csv`, `E3/resultados/resumen.txt`, 8 figuras PNG (4 mejores + 4 peores por CD).

**Diagnóstico visual:** las predicciones son nubes difusas sin forma reconocible — el modelo aprendió *dónde* están los puntos pero no *cómo* estructurarlos. El mejor caso (CD=0.033) tiene cierta forma; el peor (CD=0.182, bowl fragmentado) falla completamente.

**Causas probables:**
1. Pocas épocas (100) — PCN necesita 250–400 épocas para converger
2. LR decayó demasiado rápido (×0.5 en épocas 40 y 80 → 2.5e-5 en época 97)
3. Peso coarse bajo (0.5) — el decoder coarse no aprende forma suficientemente buena, lo que arrastra al fine

**Interpretación para la memoria:** el pipeline E3 funciona de extremo a extremo. Los números son los de un primer baseline; no son comparables directamente con papers que usan CD-L2 y benchmarks distintos. El modelo v2 (más épocas, mejor schedule) debería mejorar sustancialmente.

**Acción:** iniciar entrenamiento v2 con `--resume best.pt --epochs 300 --w_coarse 1.0`. Rocío puede también probar PoinTr como alternativa con mayor capacidad.

---

### Hecho
- [x] 246 modelos .glb de Objaverse descargados → `Datos/objaverse/raw/` — `Scripts/descargar_tazas.py`
- [x] 197 modelos Objaverse normalizados (.ply) → `Datos/objaverse/limpias/` — `Scripts/filtrar_normalizar_tazas.py`
- [x] 2.547 modelos ShapeNet (mug+bowl+bottle+jar+can) descargados → `Datos/shapenet/raw/` — `Scripts/inspeccionar_shapenet.py`
- [x] 2.170 modelos ShapeNet filtrados y normalizados (.ply) → `Datos/shapenet/limpias/` — `Scripts/filtrar_normalizar_shapenet.py`
- [x] **Dataset combinado listo: 2.367 modelos .ply para entrenar**
- [x] Fantastic Breaks descargado — 150 pares roto/completo en `Datos/fantastic_breaks/` — estructura por carpeta: `model_c.ply` (completo), `model_b_0.ply` (roto), `model_r_0.ply` (fragmento), `meta_0.npz` (metadatos)
- [x] **Fantastic Breaks preprocesado** — 61 pares vasija (mug+bowl+jar+cup) submuestreados a 2.048 pts → `Datos/fantastic_breaks/procesado/` (122 archivos .npy, 3 MB) — `Scripts/preprocesar_fantastic_breaks.py` (11 jul 2026)
- [x] Hallazgo documentado: solo 6/197 Objaverse son watertight → justifica etapa 4
- [x] Cuaderno `TFM_06_Cuaderno_Tazas.ipynb` probado en local y Colab
- [x] Nerfstudio probado en Colab
- [x] Decisión de dataset: super-categoría vasijas (mug+bowl+bottle+jar+can)
- [x] `Scripts/descargar_co3d.py` creado
- [x] Docs de organización generados: TFM_09, TFM_10, TFM_11

### Pendiente — dataset (ordenado por prioridad)
- [x] **[Alta]** Descargar **Fantastic Breaks** ✅
- [ ] **[Baja — fase P1]** Descargar **CO3D** cuando el pipeline funcione en sintético y se quiera probar con fotos reales. No son modelos 3D: son vídeos/fotos de objetos con poses de cámara calculadas (~56 GB solo cup, 150+ GB completo). Entra en E1+E2, no en E3. Subset mínimo para probar: `python Scripts/descargar_co3d.py --solo cup --single_sequence_subset`
- [ ] **[Media]** Descargar **ModelNet40** cup+bowl (~500 MB, 163 modelos watertight para E3)
- [ ] **[Baja]** Descargar **Thingi10K** (~3 GB) — puede esperar a que el pipeline funcione
- [ ] Contar watertight en ShapeNet (comparar con 6/197 de Objaverse)
- [ ] Ampliar Objaverse a bowl+bottle+jar+can si se quiere más volumen en ese dataset

### Pendiente — grupo y arquitectura
- [ ] Reunión de reparto: rellenar la matriz de propiedad de TFM_09
- [x] Crear repo GitHub (creado 1 jul 2026) e invitar a los 5
- [x] Reparto decidido (1 jul 2026): **Álvaro + Almu + Luis → E2** · **Raquel + Rocío → E3**
- [ ] **[Urgente]** Reunión de grupo: cerrar interfaz E2→E3 antes de empezar a programar modelos (formato exacto, nº puntos, normales sí/no)
- [ ] Cerrar interfaz E1→E2 (resolución imagen, método E2 con/sin poses, representación intermedia)
- [ ] Decidir método E2: nerfacto (NeRF) vs Zero123/LRM (image-to-3D feed-forward) — Álvaro

---

## Estructura del repositorio

```
C:\edf\TFM\
├── Documentacion\               — guías del proyecto (.md + .pdf)
├── Notebooks\                   — TFM_06_Cuaderno_Tazas.ipynb
├── Scripts\                     — descargar_tazas.py · filtrar_normalizar_tazas.py
│                                  descargar_co3d.py · inspeccionar_shapenet.py
│                                  filtrar_normalizar_shapenet.py · descargar_fantastic_breaks.py
├── Datos\
│   ├── shapenet\
│   │   ├── raw\                 — 2.547 modelos .obj (5 synsets de vasijas)
│   │   └── limpias\            — 2.170 modelos .ply filtrados y normalizados
│   ├── objaverse\
│   │   ├── raw\                 — 246 modelos .glb originales
│   │   ├── limpias\            — 197 modelos .ply filtrados y normalizados
│   │   └── metadatos\          — csv/json de metadatos
│   ├── fantastic_breaks\        — 150 pares roto/completo (carpetas 00/…149/)
│   │   └── 00/ … 149/          — model_c.ply · model_b_0.ply · model_r_0.ply · meta_0.npz
│   └── co3d\                   — (pendiente descargar)
│       ├── raw\
│       └── repo\
├── Modelos_generados\           — salidas del pipeline
├── Figuras\                     — visualizaciones
├── NOTAS_Y_HALLAZGOS.md        — este documento
└── README.md
```
