# TFM — Reconstrucción y reparación 3D de objetos rotos

De una foto de un objeto roto → malla 3D reparada → archivo STL imprimible.

**Equipo:** Raquel Roca · Rocío · Álvaro · Almu · Luis  
**Entrega:** 15 septiembre 2026

---

## Primeros pasos para nuevos miembros del equipo

### 1. Clonar el repositorio

```bash
git clone https://github.com/herredoble/TFM-reconstruccion-3D.git
cd TFM-reconstruccion-3D
```

### 2. Instalar dependencias

```bash
pip install trimesh objaverse huggingface_hub gdown
```

### 3. Obtener los datos

Los datasets NO están en GitHub (son demasiado grandes). Se obtienen de dos formas:

#### Opción A — Google Drive (recomendada para empezar rápido)

Raquel comparte por el grupo la carpeta con los datos ya procesados (~700 MB):

```
Datos/shapenet/limpias/     ← 2.170 modelos ShapeNet normalizados (.ply)
Datos/objaverse/limpias/    ← 197 modelos Objaverse normalizados (.ply)
```

Descárgala y colócala en `C:\edf\TFM\Datos\` (o ajusta la ruta en los scripts).

#### Opción B — Descargar con los scripts

**Fantastic Breaks** (150 pares roto/completo — sin autenticación):
```bash
python Scripts/descargar_fantastic_breaks.py
```
→ descarga ~8 GB automáticamente en `Datos/fantastic_breaks/`

**Objaverse** (sin autenticación):
```bash
python Scripts/descargar_tazas.py
python Scripts/filtrar_normalizar_tazas.py
```

**ShapeNet** (requiere token HF — pídelo a Raquel por WhatsApp):
```bash
# 1. Login con el token que te pase Raquel:
hf auth login   # pega el token cuando lo pida

# 2. Descarga los synsets de vasijas:
python Scripts/inspeccionar_shapenet.py --descargar

# 3. Filtra y normaliza:
python Scripts/filtrar_normalizar_shapenet.py
```

> Para tener acceso propio a ShapeNet: créate cuenta en huggingface.co,
> acepta los términos en https://huggingface.co/datasets/ShapeNet/ShapeNetCore
> y ejecuta `hf auth login` con tu propio token.

---

## Estructura del proyecto

```
TFM-reconstruccion-3D/
├── Scripts/
│   ├── descargar_tazas.py               — descarga Objaverse (tazas/vasijas)
│   ├── filtrar_normalizar_tazas.py      — limpia y normaliza modelos Objaverse
│   ├── inspeccionar_shapenet.py         — accede a ShapeNet via Hugging Face
│   ├── filtrar_normalizar_shapenet.py   — limpia y normaliza modelos ShapeNet
│   ├── descargar_fantastic_breaks.py    — descarga Fantastic Breaks (Google Drive)
│   └── descargar_co3d.py                — descarga CO3D (pospuesto a P1)
│
├── Notebooks/
│   └── TFM_06_Cuaderno_Tazas.ipynb     — tutorial interactivo (Colab/VS Code)
│
├── Documentacion/
│   ├── TFM_01_Propuesta.md              — propuesta y justificación del proyecto
│   ├── TFM_02_Guia_Completa.md          — guía completa del pipeline
│   ├── TFM_03_Guia_Blender_Herramientas.md
│   ├── TFM_05_Guia_Descarga_Datasets.md
│   ├── TFM_07_FAQ.md
│   ├── TFM_09_Organizacion_Grupo.md     — matriz de responsabilidades
│   ├── TFM_10_Guia_Git_Grupo.md         — flujo de trabajo Git para el equipo
│   └── TFM_11_Contratos_Interfaz.md     — ⚠️ PENDIENTE — contratos E1↔E2↔E3
│
├── NOTAS_Y_HALLAZGOS.md                 — log de decisiones técnicas y hallazgos
├── PLANIFICACION.md                     — sprint actual, tareas y cronograma
└── Datos/                               — NO en Git (.gitignore)
    ├── shapenet/{raw, limpias}
    ├── objaverse/{raw, limpias, metadatos}
    ├── fantastic_breaks/
    └── co3d/
```

---

## Estado de datasets

| Dataset | Estado | Modelos listos | Uso |
|---|---|---|---|
| ShapeNet (7 synsets vasijas) | ✅ Descargado y filtrado | 2.170 `.ply` | E2 + E3 entrenamiento |
| Objaverse (tazas/vasijas) | ✅ Descargado y filtrado | 197 `.ply` | E2 + E3 complemento |
| Fantastic Breaks | ✅ Descargado | 150 pares roto/completo | E3 entrenamiento |
| CO3D | ⏸ Pospuesto a P1 | — | E1+E2 fotos reales |
| Thingi10K | ⏸ Pendiente | — | E4 imprimibilidad |

---

## Reparto del equipo

| Etapa | Responsables | Primera tarea |
|---|---|---|
| **E2 — Reconstrucción 3D** | Álvaro, Almu, Luis | Álvaro: research spike NeRF vs feed-forward · Almu: pipeline de juguete · Luis: métricas |
| **E3 — Reparación** | Raquel, Rocío | Raquel: preprocesar Fantastic Breaks (submuestreo a 2.048 pts) · Rocío: arquitectura baseline |

> ⚠️ **Antes de empezar a programar modelos:** cerrar el contrato de interfaz E2→E3
> (formato exacto, nº puntos, normales sí/no). Ver `TFM_11_Contratos_Interfaz.md`.

---

## Documentación clave

| Documento | Para quién |
|---|---|
| `PLANIFICACION.md` | Todo el equipo — tareas urgentes y cronograma |
| `TFM_09_Organizacion_Grupo.md` | Todo el equipo — roles y responsabilidades |
| `TFM_10_Guia_Git_Grupo.md` | Todo el equipo — cómo trabajar con Git/PR |
| `TFM_11_Contratos_Interfaz.md` | E2 + E3 — formato de datos entre etapas |
| `TFM_03_Guia_Blender_Herramientas.md` | E1 + E4 — Blender, MeshLab, slicers |
| `NOTAS_Y_HALLAZGOS.md` | Referencia técnica completa |
