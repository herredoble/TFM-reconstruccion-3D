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

### H17 — Comparativa de estrategias de generación de roturas sintéticas
*(14 ago 2026 — Raquel)*

---

#### ¿Por qué necesitamos generar roturas sintéticas?

Los modelos de shape completion (PCN, PoinTr, SnowFlakeNet) aprenden a reconstruir
una nube de puntos completa a partir de una parcial. Para entrenar bien necesitan miles
de pares `(roto → completo)`. Fantastic Breaks solo aporta 61 pares reales de vasijas;
el resto los generamos artificialmente a partir de modelos 3D completos de ShapeNet y Objaverse.

La técnica que usamos para simular la rotura determina directamente qué aprende el modelo:
si las roturas son poco realistas, el modelo aprende patrones que no existen en la realidad.

---

#### Estrategia 1 — Corte por plano (v1, la que usamos hasta ahora)
*Script: `Scripts/generar_roturas_sinteticas.py` — usada en PCN v1 y v3*
*Datos: `Datos/sintetico/roturas/` — 2.367 pares*

**Cómo funciona:**
1. Se elige una dirección aleatoria en el espacio 3D.
2. Cada punto del modelo se proyecta sobre esa dirección → da un número.
3. Se elimina la mitad "por encima" del plano: los puntos con proyección más alta.
4. El porcentaje eliminado es aleatorio entre el **25% y el 75%**.
5. La superficie de corte es un plano matemáticamente perfecto.

```
       plano de corte
            │
  [queda]   │   [se elimina]
    ○ ○ ○   │   ○ ○
    ○ ○     │     ○ ○
    ○ ○ ○   │   ○
```

**Por qué es válida:** es la técnica estándar en los papers del campo (PCN, FoldingNet, GRNet).
Es simple, reproducible y cubre bien el caso "la vasija se partió en dos trozos grandes".

**Problemas detectados (14 ago 2026):**
1. **Roturas demasiado grandes**: el 75% máximo genera nubes casi vacías, poco realistas.
   Una vasija rota de verdad rara vez pierde más del 50% del material.
2. **Formas extrañas en los datos fuente**: algunos `.ply` tienen múltiples componentes
   desconectados (asa suelta, artefactos flotantes). trimesh los concatenaba, generando
   nubes sin forma de vasija. El filtro de la v1 era solo "¿tiene más de 10 puntos?" → insuficiente.
3. **Superficie de corte irreal**: el plano perfecto no existe en cerámica rota.
   Una rotura real tiene una superficie rugosa e irregular.

---

#### Estrategia 2 — Mezcla de modos con filtro geométrico (v2, la que usamos ahora)
*Script: `Scripts/generar_roturas_sinteticas.py` (actualizado 14 ago 2026)*
*Notebook: `E3/generar_roturas_standalone.ipynb` — ejecutado 15 ago 2026 en Colab A100 High RAM*
*Datos: `Datos_E2_E3/General/sintetico_roturas_v2/` en Drive — **2.299 pares generados** ✅*

**Cambios respecto a v1:**

| Aspecto | v1 | v2 |
|---------|----|----|
| Lector de .ply | trimesh (carga mesh completo: vértices+caras+topología → 300-500 MB/modelo) | **plyfile** (solo vértices x,y,z → ~2 MB/modelo) |
| Carga de componentes | Concatena todos los componentes del mesh | Todos los vértices (archivos ya limpios) |
| Filtro geométrico | Ninguno (solo "≥10 puntos") | PCA eigenvalores: descarta formas planas/lineales |
| Tamaño de rotura | **25%–75%** eliminado | **15%–50%** eliminado |
| Superficie de corte | Plano perfecto | Plano con jitter Gaussiano σ=0.05 → rugoso |
| Modos de fractura | Solo plano | **3 modos** con probabilidades |

**Los tres modos de fractura (elegidos aleatoriamente por modelo):**

**Modo PLANO (40% de los pares)** — igual que v1 pero con rugosidad:
- Un semiplano aleatorio + ruido Gaussiano en la superficie de corte.
- Simula: taza partida en dos golpes grandes, rotura limpia de borde.

**Modo CHIP (40% de los pares)** — nuevo:
- Se elige un punto aleatorio de la superficie como "punto de impacto".
- Se eliminan todos los puntos dentro de una esfera de radio r alrededor de ese punto.
- El radio se ajusta para eliminar entre 15% y 50% de puntos.
- Superficie del chip con jitter Gaussiano → borde irregular.
- Simula: **golpe puntual** — mella, esquirla, desconche de cerámica.
```
    ○ ○ ○ ○ ○ ○
    ○ ○ ○   ○ ○   ← hueco esférico = golpe
    ○ ○ ○ ○ ○ ○
```

**Modo CUÑA (20% de los pares)** — nuevo:
- Dos planos aleatorios que se intersectan forman una cuña triangular.
- Se elimina la zona "dentro" de ambos planos a la vez.
- Simula: **trozo de borde que se desprende**, esquirla lateral.
```
    ○ ○ ○ ○
    ○ ○ ○ ╲ ╲   ← cuña eliminada
    ○ ○ ╲ ╲
```

**Filtro geométrico (nuevo en v2):**
- Se calcula la PCA de los vértices normalizados del modelo.
- Si el ratio eigenvalor_mínimo / eigenvalor_máximo < 0.01 → se descarta.
- Detecta: formas planas (láminas, platos) y formas lineales (agujas, barras).
- En el log aparece como `[FILT]` con el motivo.

**Carpeta de salida:** `Datos_E2_E3/General/sintetico_roturas_v2/` en Drive
(separada de `sintetico/roturas/` para poder comparar el impacto en el entrenamiento)

**Resultado de la ejecución (15 ago 2026):**

| Dataset | Modelos entrada | Pares generados | Filtrados PCA | Errores |
|---------|----------------|----------------|--------------|---------|
| ShapeNet | 2.170 | 2.168 | 1 | 1 |
| Objaverse | 197 | 197 | 0 | 0 |
| **Total** | **2.367** | **2.299** | **1** | **1** |

- Tasa de éxito: 99,95% en ShapeNet, 100% en Objaverse
- Tamaño total en Drive: **113,6 MB** (4.598 archivos .npy)
- Shape verificada: `(2048, 3)` float32 ✓
- Notebook: `E3/generar_roturas_standalone.ipynb`

**Nota técnica — crash de RAM resuelto (15 ago 2026):**
El notebook petaba con OOM (Out Of Memory) en Colab incluso con A100 + High RAM porque `trimesh.load` + `split()` construye la topología completa del mesh (vértices + caras + aristas + grafos de adyacencia + caché interna), consumiendo 300-500 MB por modelo grande. Con 2.367 modelos en bucle, la RAM se agotaba. Solución: sustituir trimesh por `plyfile`, que lee solo las columnas x,y,z del bloque vertex del .ply sin construir topología → ~2 MB por modelo independientemente del tamaño de la malla. Fix aplicado en la Celda 3 del notebook.

---

#### Estrategia 3 — Oclusión por viewpoint (enfoque PoinTr) — NO la usamos
*Referencia: "PoinTr: Diverse Point Cloud Completion with Geometry-Aware Transformers" (Yu et al., 2021)*

**Cómo funciona:**
1. Se elige un punto de vista aleatorio (una dirección en la esfera).
2. Se simula lo que vería una cámara de profundidad (LiDAR, depth sensor) desde ese ángulo.
3. Se conservan solo los puntos **visibles** desde ese punto de vista → los del lado frontal.
4. Los puntos del lado posterior quedan ocultos → son la "parte que falta".

```
    cámara →  [visible]  [oculto]
              ○ ○ ○ ○   (no se ve)
              ○ ○ ○ ○
```

En la práctica, esto es equivalente a un corte por plano pero manteniendo solo
la mitad "hacia la cámara", en lugar de la mitad "de espaldas al corte" que hacemos nosotros.
La diferencia sutil es que PoinTr puede simular profundidad (puntos más cercanos a la cámara
se ven mejor), nosotros simplemente cortamos.

**Por qué PoinTr lo usa:**
PoinTr está diseñado para el caso de uso de **escaneado 3D incompleto**: tienes un objeto
y lo has escaneado con un sensor de profundidad desde un único ángulo.
La parte que no se ve (la cara posterior) es la que el modelo debe completar.
Ese escenario es realista para robótica y escaneado industrial.

**Por qué NOSOTROS NO lo usamos:**
Nuestro caso de uso es diferente: **vasijas físicamente rotas** (cerámica, porcelana).
Una vasija rota no tiene "cara oculta por oclusión" — tiene trozos que literalmente
ya no están. El hueco es físico, no geométrico.

| | Oclusión (PoinTr) | Rotura física (nuestro caso) |
|--|-------------------|------------------------------|
| ¿Qué simula? | Sensor no vio esa parte | El material ya no existe |
| Forma del hueco | Siempre hacia un lado (el de atrás) | Cualquier zona del objeto |
| Realismo para vasijas | Bajo — no corresponde al daño real | Alto |
| Usado en | Escaneado industrial, robótica | Restauración, arqueología, control de calidad |

**Conclusión:** el enfoque de PoinTr es válido en su dominio pero inadecuado para el nuestro.
Nuestras roturas v2 (mezcla de plano + chip + cuña) son más representativas del daño
real en cerámica que la oclusión por viewpoint.

---

#### Resumen comparativo de los tres enfoques

| | v1 (plano) | v2 (mezcla) | PoinTr (viewpoint) |
|--|-----------|-------------|-------------------|
| Modelos entrenados | PCN v1, PCN v3 | **PCN v4, PCN v5** ✅ | — |
| Datos | `sintetico/roturas/` (2.367 pares) | `sintetico_roturas_v2/` (**2.299 pares** ✅) | — |
| Realismo para vasijas | Medio | **Alto** | Bajo |
| Complejidad impl. | Baja | Media | Baja |
| Estándar en papers | Sí (PCN, FoldingNet) | No (mejora propia) | Sí (PoinTr, SnowFlakeNet) |
| Resultado PCN | CD=0.0665, F=0.024 | **CD=0.0630, F=0.0257** ✅ (v5 con fix centroide) | — |

---

### H18 — PCN v4: resultados y comparativa con v3
*(15 ago 2026 — Raquel)*

Entrenamiento completado en Google Colab A100 (~2.5 horas). Best epoch: **480/500**.

**Configuración v4:**
- Datos: `sintetico_roturas_v2` (2.299 pares, modos plano+chip+cuña) + Fantastic Breaks (61 pares) = **2.360 total**
- GPU: NVIDIA A100-SXM4-40GB (42.4 GB VRAM)
- Filtro outliers σ=2.5 activo en `dataset.py`
- Épocas: 500 · LR: 1e-4 · lr_decay: 100 · batch: 64 · **w_coarse: 1.0**

**Resultados:**

| Métrica | PCN v3 (ref) | PCN v4 | Cambio |
|---------|-------------|--------|--------|
| CD-L1 media | 0.066536 | **0.064096** | −3.7% ✓ |
| CD-L1 mediana | 0.062840 | **0.056996** | −9.3% ✓✓ |
| CD-L1 std | 0.021672 | 0.028339 | +30.8% (↑ varianza) |
| CD-L1 mejor | 0.028372 | **0.027344** | −3.6% ✓ |
| CD-L1 peor | 0.166181 | 0.229480 | +38% (↑ peor caso) |
| F-Score media | 0.0243 | 0.0236 | −2.9% (≈ igual) |
| F-Score mediana | 0.0115 | **0.0123** | +7% ✓ |
| Best epoch | 347/400 | 480/500 | — |
| Muestras test | 237 | 236 | — |

**Análisis:**

1. **Mejora real pero modesta en media (−3.7%).** La mediana mejora más (−9.3%), lo que indica que el modelo es claramente mejor en los casos típicos. La media arrastra outliers extremos.

2. **Varianza aumenta.** El std sube de 0.021 a 0.028 y el peor caso empeora (0.166→0.229). Los nuevos modos de rotura (chip, cuña) crean algunos ejemplos más difíciles de reconstruir.

3. **F-Score prácticamente igual.** La diferencia (0.0243→0.0236) está dentro del margen de ruido estadístico. La mediana mejora ligeramente (0.0115→0.0123), consistente con la mejora en CD.

4. **El modelo no ha convergido del todo** (best en época 480 de 500). Un entrenamiento más largo podría mejorar ligeramente las métricas.

5. **Conclusión:** los datos v2 (roturas más realistas) ayudan en los casos típicos pero aumentan la dificultad en los extremos. w_coarse=1.0 no perjudicó. El siguiente paso es comparar con PoinTr v1 (entrenando en paralelo).

**Archivos:**
- Notebook: `E3/colab_entrenar_pcn_v4.ipynb`
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v4_pcn/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v4_pcn/`

---

### H19 — Desalineación de centroide entre roto y completo: causa confirmada del colapso del modelo
*(15 ago 2026 — Raquel · fix implementado en v5)*

**Observación:** Al revisar las figuras de evaluación PCN v3/v4, en los peores casos la nube rota (azul) aparece claramente desplazada respecto al GT completo (verde). El modelo predice en esos casos una **placa plana horizontal** — síntoma de colapso (no sabe qué predecir).

**Causa raíz:** El proceso de generación de roturas no re-centra la nube parcial. Al eliminar 15-50% de los puntos de un lado del objeto, el centroide de la nube restante se desplaza hacia la región intacta. Mientras tanto, el GT permanece centrado en el origen (0,0,0). El modelo tiene que aprender implícitamente esta traslación variable, lo cual es muy difícil.

Ejemplo visual (muestra 150, v3):
- Rota: fragmento pequeño, centroide ~(−0.4, 0, 0)
- GT: bol completo, centroide ~(0, 0, 0)
- Predicción: placa plana (CD=0.181, F-Score=0.006)

Ejemplo del mejor caso (muestra 37, v3):
- Rota: la rotura es leve → centroide no muy desplazado
- Predicción: razonablemente correcta (CD=0.033, F-Score=0.122)

**El patrón es inequívoco:** a mayor desalineación de centroide, peor predicción. Es la causa principal de los outliers extremos (CD=0.229 en v4).

**Fix implementado en `E3/dataset.py` (`CENTRAR_EN_ROTO=True`):**

```python
# En __getitem__, tras cargar roto y completo:
roto_mean = roto.mean(axis=0)        # centroide del fragmento
roto      = roto     - roto_mean     # centrar fragmento en (0,0,0)
completo  = completo - roto_mean     # desplazar GT al mismo frame
```

**Por qué es correcto:**
- El modelo siempre recibe una entrada centrada → representación consistente
- El GT está expresado en el frame del fragmento (no del objeto original)
- En inferencia: centrar el fragmento roto real → predecir → la salida ya está en el frame correcto
- Es el preprocesado estándar en FoldingNet, GRNet y otras implementaciones de shape completion

**Impacto real en v5 (ver H20):**
- F-Score +8.9% (mejora más significativa — punto a punto más precisos)
- CD media −1.8% (mejora más modesta de lo esperado)
- std −6.4% (reducción de varianza ✓)
- Los casos patológicos más extremos persisten (muestra 22, CD=0.222)

**Estado:** ✅ implementado en `E3/dataset.py` · re-entrenado como PCN v5.

---

### H20 — PCN v5: resultados con fix de centroide
*(15 ago 2026 — Raquel)*

Entrenamiento completado en Google Colab A100 (~2.5 horas). Best epoch: **445/500**.

**Configuración v5:**
- **Cambio clave:** `CENTRAR_EN_ROTO=True` en `dataset.py` (fix H19)
- Datos: mismos que v4 — `sintetico_roturas_v2` (2.299 pares) + Fantastic Breaks (61) = 2.360 total
- GPU: NVIDIA A100-SXM4-40GB (42.4 GB VRAM)
- Épocas: 500 · LR: 1e-4 · lr_decay: 100 · batch: 64 · w_coarse: 1.0

**Resultados — comparativa v3 / v4 / v5:**

| Métrica | v3 | v4 | v5 | Δ v4→v5 | Δ v3→v5 |
|---------|----|----|----|----|-----|
| CD-L1 media | 0.066536 | 0.064096 | **0.062954** | −1.8% | −5.4% |
| CD-L1 mediana | 0.062840 | 0.056996 | **0.057170** | +0.3% | −9.1% |
| CD-L1 std | 0.021672 | 0.028339 | **0.026518** | −6.4% ✓ | +22% |
| CD-L1 mejor | 0.028372 | 0.027344 | 0.027497 | +0.6% | −3.1% |
| CD-L1 peor | 0.166181 | 0.229480 | 0.222242 | −3.2% | +34% |
| F-Score media | 0.0243 | 0.0236 | **0.0257** | +8.9% ✓✓ | +5.8% |
| Best epoch | 347/400 | 480/500 | **445/500** | — | — |

**Análisis:**

1. **F-Score +8.9%: el logro más importante de v5.** El fix de centroide permite que el modelo prediga puntos en las posiciones correctas, no en un promedio desplazado. Esta métrica mide precisión punto a punto y es más sensible al desplazamiento que CD.

2. **CD media sigue la tendencia (−1.8%).** La mejora es más modesta que la esperada (se estimó −10-20%). El motivo es que los casos patológicos más extremos no desaparecen: muestra 22 sigue con CD=0.222. Estos casos corresponden probablemente a modos chip+cuña con roturas muy extremas donde el fragmento tiene muy pocos puntos y forma irregular.

3. **Varianza se reduce (std −6.4% vs v4).** La distribución de errores se estrecha ligeramente, confirmando que el centroide desalineado era fuente de varianza. Aún está por encima de v3 (0.021) porque los datos v2 tienen más diversidad de rotura.

4. **Convergencia más rápida (445 vs 480 épocas).** El modelo encuentra un mínimo antes, lo que sugiere que el fix simplifica el problema de aprendizaje.

5. **Casos patológicos persisten.** El peor caso (CD=0.222, muestra 22) sigue siendo patológico. Probablemente corresponde a roturas extremas (>45% de puntos eliminados, modo chip) donde el fragmento tiene muy pocos puntos informativos. Posibles mejoras futuras: limitar aún más el % de rotura, o aumentar el n_puntos del fragmento.

**Conclusión:** v5 es el mejor modelo PCN en F-Score y CD media. La centración de centroide ayuda, especialmente en precisión de posición (F-Score). La arquitectura PCN parece estar cerca de su límite para este dataset — PoinTr (transformer) es el siguiente paso natural.

**Archivos:**
- Notebook: `E3/colab_entrenar_pcn_v5.ipynb`
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v5_pcn/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v5_pcn/`

---

### H21 — PoinTr: extensiones CUDA no compilan en Colab → mocks en sys.modules
*(15 ago 2026 — Raquel)*

**Síntoma:** Al ejecutar la Celda 7 del notebook PoinTr v1, dos errores encadenados:

```
KeyError: 'PoinTr is not in the models registry'
ModuleNotFoundError: No module named 'pointnet2_ops'
RuntimeError: No se pudo inicializar PoinTr.
```

**Causa raíz:** PoinTr tiene dos extensiones CUDA que importa a nivel de módulo (en el propio código fuente, no solo en el training loop):
1. `chamfer_dist` — Chamfer Distance en CUDA
2. `pointnet2_ops` / `pointnet2_ops_lib` — FPS (Furthest Point Sampling), ball query, KNN

Si cualquiera de las dos falla al compilar en Colab, el código fuente del modelo no puede importarse. Como consecuencia, el decorador `@MODELS.register_module()` nunca se ejecuta y PoinTr no queda registrado → `KeyError: 'PoinTr is not in the models registry'`.

**Extensiones que fallan:**
- `chamfer_dist`: resuelto en sesión anterior con mock
- `pointnet2_ops`: nuevo error de esta sesión — `No module named 'pointnet2_ops'`

**Fix: inyectar mocks en sys.modules ANTES de importar PoinTr**

Para `pointnet2_ops`, implementar en PyTorch puro las 6 operaciones que PoinTr usa:

| Operación | Descripción | Implementación |
|-----------|-------------|---------------|
| `furthest_point_sample(xyz, n)` | FPS clásico | Loop sobre n iteraciones, O(N·n) |
| `gather_operation(feat, idx)` | Indexing por índices | `feat.gather(2, idx)` |
| `ball_query(r, k, xyz, q)` | Vecinos en radio r | `torch.cdist` + `argsort` |
| `grouping_operation(feat, idx)` | Agrupación local | `feat.gather` + reshape |
| `three_nn(unknown, known)` | 3 vecinos más cercanos | `torch.cdist.topk(3)` |
| `three_interpolate(feat, idx, w)` | Interpolación ponderada | gather + suma pesada |

Las implementaciones en PyTorch puro son matemáticamente idénticas a las CUDA; entre 2-3x más lentas por batch. Con batch=32 y A100, el impacto es tolerable para 300 épocas.

**Código del fix** (aplicado en `E3/colab_entrenar_pointr_v1.ipynb`, Celda 7, antes de cualquier import de PoinTr):

```python
if 'pointnet2_ops' not in sys.modules:
    _utils = types.ModuleType('pointnet2_ops.pointnet2_utils')
    _utils.furthest_point_sample = _fps     # loop FPS
    _utils.gather_operation      = _gather_op
    _utils.ball_query            = _ball_query  # cdist + argsort
    _utils.grouping_operation    = _grouping_op
    _utils.three_nn              = _three_nn
    _utils.three_interpolate     = _three_interp
    sys.modules['pointnet2_ops']                 = _pm2
    sys.modules['pointnet2_ops.pointnet2_utils'] = _utils
```

**Resultado esperado:**
- `[OK] Mock pointnet2_ops inyectado` → modelo se importa
- `@MODELS.register_module()` corre → PoinTr queda en el registro
- `build_model_from_cfg({'NAME': 'PoinTr', ...})` → OK
- Entrenamiento arranca normalmente

**Estado:** fix aplicado en Celda 7 del notebook.

**Errores adicionales resueltos (16 ago 2026):**

- **`knn_cuda` instalado pero falla** — La versión compilada de `knn_cuda` hace `assert torch.cuda.is_available()` en `__init__`. Fix: forzar siempre nuestro mock con `_force('knn_cuda', ...)` (sobreescribe cualquier versión existente en sys.modules).
- **`PoinTr.py` línea 25: `.cuda()` hardcodeado** — La clase `Fold.__init__` hace `self.folding_seed = torch.cat([a, b], dim=0).cuda()`. Si no hay GPU disponible (runtime CPU o T4 sin asignar), lanza `AssertionError: Torch not compiled with CUDA enabled`. Fix: parchear todos los `.py` de `/content/PoinTr/models/` reemplazando `.cuda()` por `.to(device)` ANTES de importar los módulos.
- **Sin unidades GPU en Colab Pro** — Tanto A100 como T4 agotados. Fix temporal: versión `_prueba` del notebook que corre 2 épocas / 200 muestras en CPU para verificar el código.

**Verificación 16 ago 2026:** `colab_entrenar_pointr_v1_prueba.ipynb` ejecutado en CPU sin errores. Prueba OK — val loss=0.1408 en época 2 (no comparable, solo verifica el pipeline).

**Pendiente:** lanzar `colab_entrenar_pointr_v1.ipynb` cuando se repongan unidades T4/A100.

---

### H22 — PoinTr v2: primer entrenamiento completo con datos filtrados
*(24 ago 2026 — Raquel)*

Primer entrenamiento PoinTr con datos limpios (blacklist de 1.958 pares excluidos de sintetico_roturas_centradas).

**Configuración v2:**
- Datos: 402 pares limpios — sintetico_roturas_centradas (filtrado) + Fantastic Breaks (61 pares)
  - Train: 321 | Val: 40 | Test: 41 (batches: 11/2/2)
- GPU: Tesla T4 (15.6 GB)
- Épocas: 150 · LR: 1e-4 · W_coarse: 0.5 · batch: 32
- Optimizer: AdamW · Scheduler: CosineAnnealingLR

⚠️ **Contaminación en épocas 1-30:** La lógica de resume encontró un checkpoint epoch_030 de un primer intento donde sintetico no se había cargado (ruta incorrecta: `sintetico_roturas_v2` en lugar de `sintetico_roturas_centradas`). Esas primeras 30 épocas se entrenaron solo con los 61 pares de Fantastic Breaks. A partir de época 31, el modelo recibió los 402 pares correctos y se recuperó. **A pesar de ello, superó a PCN v5.**

**Resultados — test set (41 muestras):**

| Métrica | PCN v5 (ref) | PoinTr v2 | Δ |
|---------|-------------|-----------|---|
| CD-L1   | 0.0630      | **0.0533** | −15.3% |
| F-Score | 0.0257      | **0.3278** | +12.7× |
| Best epoch | 445/500  | 150/150   | — |

**Análisis:**

1. **CD −15.3%: mejora sustancial pese a contaminación.** El transformer (PoinTr) supera claramente a PointNet+folding (PCN), incluso con los primeros 30 epochs entrenados solo en 61 pares de Fantastic Breaks.

2. **F-Score ×12.7: salto cualitativo.** Mide precisión punto a punto (threshold=0.01). PoinTr coloca puntos mucho más cerca de la geometría real — métrica más relevante para calidad visual de la reconstrucción.

3. **Modelo aún en mejora a época 150.** Las curvas muestran train y val bajando en la última época → v3 con 200 épocas y sin contaminación puede mejorar más.

4. **Dataset pequeño post-filtrado.** Solo 402 pares (el blacklist eliminó el 83% del sintetico). El modelo generaliza bien dado el volumen limitado.

**Conclusión:** PoinTr supera PCN en ambas métricas incluso con entrenamiento parcialmente contaminado. La ventaja del transformer sobre PointNet+folding queda confirmada. Próximo: PoinTr v3 con `CENTRAR_EN_ROTO=False` (alineación original roto/completo) y 200 épocas limpias.

**Archivos:**
- Notebook: `E3/colab_entrenar_pointr_v2.ipynb`
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v2_pointr/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v2_pointr/`

---

### H23 — Descubrimiento alineación Fantastic Breaks + PoinTr v3 y v4
*(25 ago 2026 — Raquel, Rocío)*

**Problema identificado:** Las figuras rotas en Fantastic Breaks v1 no coinciden en posición con su objeto completo correspondiente. El fragmento roto estaba en un frame de coordenadas diferente al objeto completo, lo que significa que el modelo aprendía a predecir puntos en ubicaciones inconsistentes con la pieza rota de entrada.

**Solución de Rocío:** Corrigió el preprocesado de los 61 pares de Fantastic Breaks y guardó la versión corregida en Drive → `Datos_E2_E3/General/Fantastik_Break_Procesado_v2`. En la v2 el fragmento roto se superpone correctamente al objeto completo (mismo frame de coordenadas).

**PoinTr v3 — resultados parciales:**
- Configuración: 402 pares (sintetico filtrado + FB v1), CENTRAR_EN_ROTO=False, 200 épocas
- GPU: Tesla T4
- Mejor época: 155/200 · mejor val loss: 0.109349
- Evaluación (test CD/F-Score): pendiente — sesión Colab terminó antes de ejecutar celda 9
- Archivos: `E3/colab_entrenar_pointr_v3.ipynb` · Drive → `modelos/v3_pointr/`

**PoinTr v4 — experimento de calidad de datos:**
- Solo Fantastic Breaks v2 (61 pares con alineación correcta, sin datos sintéticos, sin blacklist)
- CENTRAR_EN_ROTO=False (los datos ya están correctamente alineados por Rocío)
- 300 épocas · batch=32 · ~48 pares train (~2 batches/época)
- GPU: Tesla T4 · best época: 285/300

**Resultados v4 — test set (7 muestras):**

| Métrica | PCN v5 | PoinTr v2* | PoinTr v4 |
|---------|--------|------------|-----------|
| CD-L1   | 0.0630 | 0.0533     | **0.0569** |
| F-Score | 0.0257 | 0.3278*    | 0.0285    |

*v2 tenía CENTRAR_EN_ROTO=True que inflaba el F-Score (tarea artificialmente más fácil)

**Análisis:**
1. **CD=0.0569 con solo 61 pares reales supera a PCN v5 con ~400 pares** → datos bien alineados valen más que cantidad en este rango.
2. **F-Score bajo (0.0285) no indica regresión respecto a v2** — el 0.3278 de v2 era por CENTRAR_EN_ROTO=True; 0.0285 vs 0.0257 (PCN v5) es comparable y consistente.
3. **7 muestras de test** → varianza muy alta, resultados no estadísticamente fiables.
4. **Best epoch 285/300** → sin overfitting claro; el modelo seguía aprendiendo hasta el final.
5. **El sintético siempre estuvo bien alineado** (los fragmentos se cortan del propio mesh completo). El problema era específico del preprocesado de Fantastic Breaks v1.

**Conclusión:** La calidad de datos supera a la cantidad. Próximo paso natural: PoinTr v5 = FB v2 + sintético filtrado (blacklist) con CENTRAR_EN_ROTO=False, para tener ~402 pares correctamente alineados y una evaluación estadísticamente válida.

**Archivos:**
- Notebook: `E3/colab_entrenar_pointr_v4.ipynb`
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v4_pointr_fbv2/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v4_pointr_fbv2/`

---

### H25 — Timeline de limpieza de datos: qué usó cada experimento
*(27 ago 2026 — Raquel · para contexto de resultados y redacción)*

Esta tabla es clave para interpretar los resultados: los experimentos anteriores a PoinTr v4 usaron datos con problemas de alineación o ruido que explican las métricas inferiores.

#### Estado de los datasets por versión

| Experimento | FB usado | Objaverse | Sintético | CENTRAR_EN_ROTO | ¿Datos limpios? |
|-------------|----------|-----------|-----------|-----------------|-----------------|
| PCN v1 | FB v1 ❌ desalineado | — | sint_v1 (solo plano) | False | ❌ |
| PCN v3 | FB v1 ❌ desalineado | — | sint_v1 (solo plano) | False | ❌ |
| PCN v4 | FB v1 ❌ desalineado | — | sint_v2 (plano+chip+cuña) | False | ❌ FB |
| PCN v5 | FB v1 ❌ desalineado | — | sint_v2 | **True** (compensa parcialmente) | ❌ FB |
| PoinTr v2 | FB v1 ❌ desalineado | — | sint_centradas_filtrado | **True** → F-Score inflado | ❌ FB + F inflado |
| PoinTr v3 | FB v1 ❌ desalineado | — | sint_centradas_filtrado | False | ❌ FB desalineado |
| PoinTr v4 | **FB v2 ✅** | — | — (solo reales) | False | ✅ primer exp honesto |
| PoinTr v5_fb_obj | **FB v2 ✅** | **Ob v2 ✅** | — | False | ✅ |
| PoinTr v5_obj | — | **Ob v2 ✅** | — | False | ✅ |

#### Qué significa cada problema

- **FB v1 desalineado:** Los fragmentos rotos y la pieza completa están en frames de coordenadas distintos. El modelo intenta predecir puntos en el lugar equivocado del espacio. Causa de F-Score bajo y CD alto en PCN.
- **CENTRAR_EN_ROTO=True en PoinTr v2:** Centra ambas nubes en el centroide del fragmento antes de pasarlas al modelo. El GT queda artificialmente "cerca" del roto → F-Score 0.3278 irreal (×12 vs honesto). Útil para entrenar PCN (donde no había datos bien alineados), distorsionante en PoinTr.
- **sint_v1 (solo plano):** Roturas demasiado grandes (25-75%), superficie de corte perfecta. Poco realista.
- **sint_centradas_filtrado:** Sintético con blacklist (1.958 pares malos eliminados). Solo 402 pares útiles de los 2.367 originales. El filtro era necesario porque el sintético v1 tenía muchos modelos con artefactos.

#### Carpetas de datos en Drive (estado a 27 ago 2026)

**En uso activo (experimentos v5+):**
- `Datos_E2_E3/General/Fantastik_Break_Procesado_v2/` — 120 npy (61 pares reales, Rocío-cleaned)
- `Datos_E2_E3/General/roturas_Objaverse_v2/` — 794 npy (397 pares, Rocío-cleaned)
- `Datos_E2_E3/General/shapenet_roturas/` — 4208 npy (2104 pares, sin usar en entrenamiento aún)

**Obsoletas / sustituidas (no borrar, son referencia histórica):**
- `Fantastik_Break_Preprocesado/` — FB v1, sustituida por v2
- `Objaverse_limpias/` — 197 ply originales, sustituida por v2 (131 ply Rocío-cleaned)
- `sintetico_roturas/` — v1 del sintético (plano simple), sustituida

**No útiles (vacías o irrelevantes):**
- `Shapenet_limpias/` — 0 bytes, vacía
- `v2_pcn/` y `v5_pointr_objaverse_fbv2/` en modelos/ — carpetas vacías

#### Impacto en la memoria del TFM

Para la redacción: los resultados de PCN v1-v5 y PoinTr v2-v3 son con datos no completamente limpios. La comparación honesta empieza en **PoinTr v4** (primer experimento con datos correctamente alineados). Los resultados de v4/v5_fb_obj/v5_obj son los que representan el rendimiento real del sistema.

---

### H26 — PoinTr v5_obj: nuevo MEJOR resultado (CD=0.0306)
*(27 ago 2026 — Raquel)*

**Configuración:**
- Dataset: solo Objaverse v2 (397 pares, Rocío-cleaned) — sin Fantastic Breaks
- Train: 317 | Val: 39 | Test: 41
- GPU: A100 · 300 épocas · mejor época: 257/300
- CENTRAR_EN_ROTO=False

**Resultados — test set (41 muestras):**

| Métrica | PCN v5 | PoinTr v4 | PoinTr v5_fb_obj | **PoinTr v5_obj** |
|---------|--------|-----------|------------------|-------------------|
| CD-L1   | 0.0630 | 0.0569    | 0.0323           | **0.0306**        |
| F-Score | 0.0257 | 0.0285    | 0.2548           | **0.2701**        |
| N test  | —      | 7         | 47               | 41                |

**Análisis:**
1. **Añadir FB v2 a Objaverse empeora ligeramente el resultado** (0.0323 → 0.0306 al quitar FB). Los 60 pares reales de FB, aunque correctamente alineados, introducen varianza o distribución diferente que no ayuda al modelo.
2. **Solo Objaverse es suficiente** para superar todo lo anterior. 397 pares limpios de Rocío baten a cualquier combinación anterior.
3. **F-Score más alto con solo Ob** (0.2701 vs 0.2548) — los datos más homogéneos producen predicciones más precisas punto a punto.
4. **Mejor época 257/300** — el modelo convergió antes que v5_fb_obj (289), coherente con un dataset más limpio y homogéneo.

**Conclusión:** La limpieza y alineación de Objaverse por Rocío es el mayor factor de mejora del proyecto. FB v2 añade variedad pero también ruido; para el siguiente experimento (v5_all con ShapeNet), hay que monitorizar si ShapeNet (parcialmente limpio) mejora o empeora.

**Archivos:**
- Notebook: `E3/colab_entrenar_pointr_v5.ipynb` (flags: `USAR_OBJAVERSE=True, USAR_FB_V2=False`)
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v5_obj/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v5_obj/metricas.json`

---

### H27 — Auditoría Drive (27 ago 2026): estado y espacio ocupado
*(27 ago 2026 — Raquel · registro para no borrar pero saber qué hay)*

**Resumen del espacio ocupado en Drive (E3/Raquel/modelos/):**

| Carpeta | Tamaño | Contenido | Decisión futura |
|---------|--------|-----------|-----------------|
| v1_pcn/ | 59MB | best.pt | Borrar (CD=0.077, superado) |
| v1_pointr/ | 398MB | best.pt | Borrar (prueba inicial sin eval) |
| v2_pcn/ | 0B | vacía | Borrar |
| v2_pointr/ | 398MB | best.pt | Borrar (datos inflados) |
| v3_pcn/ | 59MB | best.pt | Conservar (referencia) |
| v3_pointr/ | **5GB** | best.pt + epoch_010..110 | Borrar epoch_*.pt; best.pt pendiente eval |
| v4_pcn/ | 59MB | best.pt | Conservar (referencia) |
| v4_pointr_fbv2/ | **12GB** | best.pt + epoch_010..300 | Borrar epoch_*.pt; conservar best.pt |
| v5_fb_obj/ | **12GB** | best.pt + epoch_010..300 | Borrar epoch_*.pt; conservar best.pt |
| v5_obj/ | **12GB** | best.pt + epoch_010..300 | Borrar epoch_*.pt; conservar best.pt |
| v5_pcn/ | 59MB | best.pt | Conservar (mejor PCN) |
| v5_pointr_objaverse_fbv2/ | 0B | vacía | Borrar (nombre antiguo de v5_fb_obj) |

**Ahorro potencial borrando epoch_*.pt y modelos obsoletos: ~40GB**

**Nota:** No se borra nada ahora. Esta tabla sirve de referencia para una limpieza futura.

---

### H24 — PoinTr v5_fb_obj: mejor resultado hasta la fecha (CD=0.0323)
*(27 ago 2026 — Raquel)*

**Configuración:**
- Datasets: Fantastic Breaks v2 (60 pares) + Objaverse v2 (397 pares) = **457 pares totales**
- Train: 365 | Val: 45 | Test: 47 — primer experimento con test estadísticamente sólido
- GPU: A100 (40 GB) · 300 épocas · mejor época: 289/300
- CENTRAR_EN_ROTO=False · LR=1e-4 · batch=32

**Resultados — test set (47 muestras):**

| Métrica | PCN v5 | PoinTr v2* | PoinTr v4 | **PoinTr v5_fb_obj** |
|---------|--------|------------|-----------|----------------------|
| CD-L1   | 0.0630 | 0.0533     | 0.0569    | **0.0323**           |
| F-Score | 0.0257 | 0.3278*    | 0.0285    | **0.2548**           |
| N test  | ?      | 41         | 7         | **47**               |

*PoinTr v2: F-Score inflado por CENTRAR_EN_ROTO=True

**Análisis:**
1. **−48.7% CD vs PCN v5** — la mayor mejora del proyecto hasta ahora.
2. **−39.4% CD vs PoinTr v2** — a pesar de que v2 tenía CENTRAR_EN_ROTO=True (ventaja artificial).
3. **Factor clave: Objaverse v2 de Rocío** — de 61 pares (v4) a 457 pares, todos correctamente alineados. La combinación de datos reales de calidad es lo que dispara el resultado.
4. **F-Score 0.2548 honesto** — sin el truco de centrar. El modelo coloca puntos cerca de la geometría real.
5. **Best epoch 289/300** — el modelo todavía mejoraba al final. Más épocas o más datos podrían mejorar más.
6. **47 muestras de test** — primer resultado estadísticamente confiable del pipeline PoinTr.

**Conclusión:** La calidad y alineación de los datos es el factor dominante. Rocío limpiar Objaverse fue más impactante que cualquier cambio de arquitectura o hiperparámetro.

**Próximos experimentos:** v5_obj (solo Objaverse), v5_all (+ ShapeNet) para aislar la contribución de cada dataset.

---

### H28 — Resultados de Rocío: PCN v3-v9 + TopNet v1 (27 ago 2026)
*(27 ago 2026 — Raquel, extraído de estado_entrenamiento.json en Drive)*

Rocío ha entrenado 3 arquitecturas distintas (PCN, TopNet) con estrategias pretrain → finetune.
Sus métricas son `mejor_val` (CD-L1 sobre validación), **no CD-L1 de test independiente** — son aproximadamente comparables pero no idénticas a nuestros resultados.

**Resumen de experimentos de Rocío:**

| Experimento | mejor_val (CD-L1 val) | Épocas | Estructura |
|-------------|----------------------|--------|-----------|
| PCN v3 | 0.0715 | 300 | Solo train |
| **PCN v4 / pretrain** | **0.0696** | 150 | Pretrain |
| PCN v8 / finetune | 0.1240 ⚠️ | 126 | Finetune fallido |
| PCN v9 / pretrain | 0.0894 | 150 | Pretrain |
| PCN v9 / finetune | 0.0859 | 550 | Finetune |
| TopNet / pretrain | 0.0805 | 124 | Pretrain |
| **TopNet / finetune** | **0.0795** | 359 | Finetune |
| TopNet / finetune_congelado | 0.0818 | 405 | Encoder congelado |

**Mejor resultado de Rocío: PCN v4/pretrain con val=0.0696**, comparable a Raquel PCN v4 (CD test=0.0641) y PCN v5 (0.0630). Las diferencias entre val y test y entre splits explican la pequeña diferencia.

**Análisis por experimento:**

1. **PCN v3 (0.0715)** — Consistente con el PCN v3 de Raquel (CD test=0.0665). Rocío entrena 300 épocas sin plateau hasta el final.

2. **PCN v4/pretrain (0.0696)** — Mejor resultado PCN de Rocío. Estrategia pretrain con curriculum de 150 épocas en 3 fases (val loss desciende en escalones cada 50 épocas, patrón típico de curriculum).

3. **PCN v8/finetune (0.1240 ⚠️)** — El finetune falló: `epocas_sin_mejora=121` con solo 126 épocas totales. El mejor valor se alcanzó en la época ~5 y luego empeoró. Posiblemente intentó adaptar a dominio FB real con demasiado cambio de distribución.

4. **PCN v9/finetune (0.0859)** — Mejoró sobre v9/pretrain (0.0894) pero peor que v4. El finetune convergió lentamente en 550 épocas.

5. **TopNet (0.0795 finetune)** — Mejor que PCN v3 (0.0715) pero peor que PCN v4 (0.0696). La estrategia congelada (0.0818) da peor resultado que finetune completo (0.0795). Pretrain (0.0805) ya alcanza buenos valores en 124 épocas.

**Conclusiones:**
- **PCN v4 de Rocío es el mejor PCN general** (0.0696 val), empatado con Raquel PCN v4.
- **TopNet es competitivo pero no supera a PCN** en sus experimentos.
- **PoinTr sigue siendo superior a ambos**: nuestro PoinTr v5_obj (CD=0.0306) es ~2.3× mejor que el mejor PCN de Rocío.
- Los checkpoints de Rocío NO tienen `metricas.json` — sus resultados vienen de `estado_entrenamiento.json` y son métricas de validación, no de test. Para publicar en la memoria del TFM habría que añadir una celda de evaluación formal sobre test set.

**Datasets usados por Rocío:** no determinados sin leer sus notebooks (`/Rocio/scripts modelos/pcn/E3_PCN_mejorado_v3.ipynb` etc.) — pendiente si se necesita para el TFM.

**Archivos:**
- Notebook: `E3/colab_entrenar_pointr_v5.ipynb`
- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v5_fb_obj/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v5_fb_obj/`

---

### H29 — PoinTr v6_obj_sn: MEJOR resultado del proyecto (CD=0.0245, F=0.4547)
*(28 ago 2026)*

**Experimento:** `v6_obj_sn` — Objaverse v2 (397p) + ShapeNet roturas (2104p), 500 épocas, A100 40GB.

| Métrica | v6_obj_sn | v5_obj (anterior mejor) | Δ |
|---------|-----------|-------------------------|---|
| CD-L1 | **0.0245** | 0.0306 | −0.0061 (−20%) |
| F-Score | **0.4547** | 0.2701 | +0.1846 (+68%) |
| Best epoch | 486/500 | 257/300 | — |
| Test n | 251 | 41 | ×6 más representativo |
| Datos | Ob v2 + SN | Ob v2 | +2104 pares ShapeNet |

**Conclusión:** Añadir ShapeNet (2104 pares) es el factor más importante hasta la fecha. La mejora en F-Score (+68%) es más llamativa que la del CD (−20%): el modelo ahora acierta en los detalles finos, no solo en la forma global.

**Observaciones de las muestras individuales:**
- ShapeNet: CD entre 0.0139 y 0.0345; F entre 0.26 y 0.63 — muy variable por objeto
- Objaverse: CD≈0.035, F≈0.08 — más difícil que ShapeNet (geometrías más diversas)
- Error coloring (umbral 0.05): 83–92% de puntos correctos
- Best epoch 486/500 → modelo casi convergido al final; ≤2 milésimas más con más épocas

**Próximo experimento sugerido:** `v6_all` (añadir FB v2) para ver si los 61 pares reales ayudan o perjudican a esta escala.

- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v6_obj_sn/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v6_obj_sn/`
- Notebook: `E3/colab_entrenar_pointr_v6.ipynb`

---

### H30 — PoinTr v6_fb_obj_sn: añadir FB v2 empeora respecto a v6_obj_sn
*(28 ago 2026)*

**Experimento:** `v6_fb_obj_sn` — FB v2 (60p) + Objaverse v2 (397p) + ShapeNet roturas (855p), 500 épocas, A100 40GB.

| Métrica | v6_fb_obj_sn | v6_obj_sn (mejor) | Δ |
|---------|-------------|-------------------|---|
| CD-L1 | 0.0297 | **0.0245** | +0.0052 (+21%) **peor** |
| F-Score | 0.3866 | **0.4547** | −0.0681 (−15%) **peor** |
| Best epoch | 407/500 | 486/500 | — |
| Test n | 132 | 251 | — |
| ShapeNet pares | 855 | 2104 | ×2.5 menos |

**Conclusión:** Añadir los 61 pares reales de Fantastic Breaks perjudica el modelo. Hay dos factores confundidos:
1. **FB v2 (60 pares reales) es más ruidoso** que los sintéticos — la muestra [6] "05_05005" (FB real) obtuvo CD=0.0724, solo 43% correctos, vs 84–93% en objetos ShapeNet.
2. **Menos ShapeNet** — Drive tenía solo 855 pares en esta sesión vs 2104 en v6_obj_sn (posible sesión Colab distinta con menos datos copiados).

Ambos factores se pueden separar con un experimento `v6_obj_sn_long` (solo Ob+SN con 2104p y más épocas), pero dado que v6_obj_sn ya es el MEJOR resultado del proyecto, se prioriza pasar a E4.

**Observación clave:** Fantastic Breaks reales son fundamentalmente más difíciles que sintéticos. Para generalizar a objetos reales se necesitaría una estrategia específica (data augmentation de ruido, o entrenamiento en dos fases).

- Modelo: Drive → `Datos_E2_E3/E3/Raquel/modelos/v6_fb_obj_sn/best.pt`
- Resultados: Drive → `Datos_E2_E3/E3/Raquel/resultados/v6_fb_obj_sn/`
- Notebook: `E3/colab_entrenar_pointr_v6_all_EJEC.ipynb`

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
- [x] **Roturas sintéticas v2 generadas** — 2.299 pares (plano+chip+cuña, filtro PCA) → `sintetico_roturas_v2/` en Drive (15 ago 2026) — `E3/generar_roturas_standalone.ipynb`
- [x] **PCN v4 entrenado** — CD=0.0641, F=0.0236, época 480/500, A100 (15 ago 2026) — `E3/colab_entrenar_pcn_v4.ipynb`
- [x] **PCN v5 entrenado** — CD=0.0630, F=0.0257, época 445/500, A100 (15 ago 2026) — fix centroide (H19) — `E3/colab_entrenar_pcn_v5.ipynb`
- [x] **PoinTr v6_obj_sn entrenado** — CD=0.0245, F=0.4547, época 486/500, A100 (28 ago 2026) — MEJOR resultado del proyecto — `E3/colab_entrenar_pointr_v6.ipynb`
- [x] **PoinTr v6_fb_obj_sn entrenado** — CD=0.0297, F=0.3866, época 407/500, A100 (28 ago 2026) — FB v2 empeora vs v6_obj_sn — `E3/colab_entrenar_pointr_v6_all_EJEC.ipynb`
- [x] **PoinTr v1 notebook listo y verificado en CPU** — prueba 2 épocas/200 muestras OK (16 ago 2026) — `E3/colab_entrenar_pointr_v1.ipynb` + `E3/colab_entrenar_pointr_v1_prueba.ipynb` — pendiente entrenamiento real con T4/A100
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
