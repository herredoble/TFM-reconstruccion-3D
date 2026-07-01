# Planificación TFM — decisiones urgentes y próximos pasos

> Documento vivo de sprint. Lo más importante está arriba.
> Raquel Roca · se actualiza con cada avance.

---

## 🔴 URGENTE ESTA SEMANA — Todo el grupo

### Cerrar el contrato de interfaz E2→E3

**Es la decisión más crítica antes de que nadie escriba una línea de modelo.** Sin esto E2 y E3 trabajan en paralelo y luego no se integran.

Preguntas a responder en reunión:

- [ ] ¿E2 entrega point cloud o malla?
- [ ] ¿Cuántos puntos? (estándar: 2.048 o 8.192)
- [ ] ¿Con normales o solo XYZ?
- [ ] ¿Cómo representamos "roto" para que E3 lo entienda?

Ver `Documentacion/TFM_11_Contratos_Interfaz.md` para el formato de referencia.

---

## 🔴 URGENTE ESTA SEMANA — Raquel (primera tarea concreta)

### 0. Subir datos procesados a Google Drive
Antes de la reunión del grupo, subir estas dos carpetas a la carpeta Drive compartida (~700 MB):
- `Datos/shapenet/limpias/`
- `Datos/objaverse/limpias/`

### 1. Preprocesado de Fantastic Breaks para E3

Tienes 150 pares roto/completo en `Datos/fantastic_breaks/`. Antes de que Rocío pueda entrenar el modelo de reparación necesita los datos en el formato correcto.

**Qué hacer:**
1. Leer `model_c.ply` (completo) y `model_b_0.ply` (roto) de cada carpeta
2. Submuestrear ambos a **2.048 puntos** (estándar en PoinTr/PCN)
3. Guardar como pares `(roto_2048.npy, completo_2048.npy)` listos para entrenar
4. Filtrar solo las clases vasija (00=mug, 02=bowl, 03=cup, 05=jar) → ~61 pares útiles

**Por qué 2.048:** los papers de shape completion (PoinTr, PCN, SnowFlakeNet) usan 2.048 puntos como input estándar. Si luego Rocío elige un modelo diferente se puede regenerar, pero 2.048 es la apuesta segura.

### 2. Subir Fantastic Breaks procesado a Drive
Una vez generados los pares `.npy` (serán ~15 MB en total), subirlos a la carpeta Drive del grupo en `fantastic_breaks_procesado/` para que Rocío pueda empezar a entrenar sin esperar a descargar los 8 GB raw.

> Fantastic Breaks raw (8 GB) NO hace falta subirlo a Drive — Rocío lo descarga con:
> `python Scripts/descargar_fantastic_breaks.py`

---

## Decisión pendiente — E2: NeRF vs feed-forward

**Álvaro hace el research spike esta semana.** Decisión antes del fin de semana.

| Opción | Ventaja | Desventaja |
|--------|---------|------------|
| NeRF clásico (nerfacto) | No necesita entrenamiento previo, funciona con pocas vistas | Tarda minutos por objeto en inferencia |
| Feed-forward (Zero123, One-2-3-45) | Inferencia rápida | Requiere más datos de entrenamiento |

Esta decisión desbloquea la implementación de Almu.

---

## Reparto del equipo

### Etapa 2 — Reconstrucción (Álvaro, Almu, Luis)

| Persona | Responsabilidad | Primera tarea |
|---------|----------------|---------------|
| **Álvaro** | Arquitectura y decisión de método | Research spike: nerfacto vs Zero123/One-2-3-45. Decisión en 1 semana |
| **Almu** | Implementación del pipeline E1+E2 | Pipeline de juguete: 5 fotos sintéticas de una taza ShapeNet → point cloud básico con nerfstudio |
| **Luis** | Métricas e integración E2→E3 | Definir métricas (Chamfer Distance, F-Score), implementar evaluación; luego encargarse del contrato E2→E3 |

### Etapa 3 — Reparación (Raquel, Rocío)

| Persona | Responsabilidad | Primera tarea |
|---------|----------------|---------------|
| **Raquel** | Datos para E3 | Script de preprocesado de Fantastic Breaks: submuestreo a 2.048 puntos, generar pares (roto, completo) listos para entrenar |
| **Rocío** | Arquitectura del modelo de reparación | Research spike: comparar PoinTr, SnowFlakeNet, PCN. Elegir el baseline. Primer entrenamiento en Fantastic Breaks |

---

## Cronograma

| Periodo | Hito |
|---------|------|
| **Semana 1-2 julio** | TODO EL GRUPO: cerrar interfaz E2↔E3, crear repo GitHub, pipeline de juguete end-to-end |
| **Semana 3-4 julio** | E2: método elegido, primer entrenamiento (ShapeNet → point cloud) · E3: Fantastic Breaks preprocesado + primer baseline entrenando |
| **Agosto** | E2: afinar modelo, evaluar con métricas · E3: mejorar modelo, augmentación sintética de roturas en ShapeNet · E4+E5: malla reparada → STL |
| **1-14 septiembre** | Integración E1+E2+E3+E4+E5 end-to-end · Demo: foto real de taza rota → STL · Memoria y presentación |
| **15 septiembre** | **Entrega** |

⚠️ **Riesgo:** la integración cae en agosto (vacaciones). Pactar disponibilidad o adelantar lo posible a julio.

---

## Estado de datasets (referencia rápida)

| Dataset | Estado | Uso |
|---------|--------|-----|
| ShapeNet (mug+bowl+bottle+jar+can) | ✅ 2.170 limpios | E2+E3 train |
| Objaverse (tazas) | ✅ 197 limpios | E2+E3 train complementario |
| Fantastic Breaks | ✅ 150 pares roto/completo | E3 train/validación — **preprocesar urgente** |
| CO3D | Pospuesto a P1 (~150 GB) | E1+E2 fotos reales — cuando el pipeline funcione |
| ModelNet40 | Pendiente (~500 MB) | E3 complemento |
| Thingi10K | Pendiente (~3 GB) | E4 imprimibilidad |
