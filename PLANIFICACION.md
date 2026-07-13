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

### ~~0. Subir datos procesados a Google Drive~~ ✅ HECHO (1 jul 2026)
~~Antes de la reunión del grupo, subir estas dos carpetas a la carpeta Drive compartida (~700 MB):~~
- ~~`Datos/shapenet/limpias/`~~
- ~~`Datos/objaverse/limpias/`~~

### ~~1. Preprocesado de Fantastic Breaks para E3~~ ✅ HECHO (11 jul 2026)

~~Tienes 150 pares roto/completo en `Datos/fantastic_breaks/`.~~

**Resultado:** 61 pares vasija (mug+bowl+jar+cup) submuestreados a 2.048 puntos.
122 archivos `.npy`, 3 MB → `Datos/fantastic_breaks/procesado/`
Script: `Scripts/preprocesar_fantastic_breaks.py`
Documentación para Rocío: `Documentacion/TFM_12_Datos_E3_Rocio.md`

**Corrección de mapping:** 03=jar (no cup), 05=cup (no jar) — verificado contra el paper.
Si hace falta ampliar: `--clases vasijas,plate` (96 pares) o `--clases todas` (150 pares).

### ~~2. Subir Fantastic Breaks procesado a Drive~~ ✅ HECHO (11 jul 2026)
~~Subir `Datos/fantastic_breaks/procesado/` a Drive del grupo como `fantastic_breaks_procesado/`.~~
Subido: 122 archivos .npy, 3 MB. Rocío puede empezar a entrenar.

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

### ~~Primer entrenamiento PCN en Fantastic Breaks~~ ✅ HECHO (13 jul 2026)

Modelo PCN entrenado con `fantastic_breaks_procesado/` (53 train / 8 val, 2.048 puntos),
170 épocas totales. Loss L1 Chamfer Distance: 0.595 → 0.137 (train), 0.216 (val).

**Pipeline completo validado:** datos → entrenamiento → evaluación → visualización funciona
de extremo a extremo sobre el contrato E2→E3.

**Hallazgo:** pese a la mejora de loss, las predicciones no muestran geometría reconocible
(distribución tipo rejilla, no superficie de vasija) — el dataset actual (61 pares) es
insuficiente para que PCN aprenda forma real. Confirma la necesidad de la augmentación
sintética con ShapeNet.

**Siguiente paso de Rocío:** esperar/generar pares sintéticos ShapeNet ampliados antes de
reentrenar; coordinar con Luis métricas estandarizadas (Chamfer Distance, F-Score).

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
