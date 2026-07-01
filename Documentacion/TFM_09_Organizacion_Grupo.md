# TFM_09 — Organización del grupo

> Cómo nos repartimos el trabajo los 5 y cómo trabajamos juntos sin pisarnos.
> Raquel Roca · Junio 2026 · Entrega: 15 sep 2026.

---

## Principio: "todos tocamos todo", pero con dueño claro

Queremos que las 5 personas aprendan el pipeline completo. El riesgo es que
"todos toquen todo" sin responsables acabe en caos justo antes de la entrega.
La solución es combinar **propiedad clara + rotación + revisión cruzada**:
cada persona es *dueña* de una etapa, *suplente* de otra, y revisa el código de
los demás. Así toca dos etapas a fondo y ve pasar todas.

---

## Capa 1 — Arranque común (todos juntos, primera semana)

Antes de repartir, las 5 hacemos **el pipeline entero sobre un ejemplo de juguete**
(1 taza: imágenes → nube → malla → reparar → STL), usando `TFM_06_Cuaderno_Tazas`
y `TFM_04_Tutorial_Practico`. Objetivo: que todo el mundo entienda el flujo de
punta a punta **antes** de especializarse. Es la forma real de "tocar todo".

---

## Capa 2 — Matriz de propiedad (primario + secundario)

Cada etapa tiene un **dueño primario** (responsable, decide e integra) y un
**secundario** (revisa los PR de esa etapa, sustituye y aprende). Cada persona
toca **dos** etapas.

| Etapa | Carga | Primario | Secundario |
|-------|-------|----------|------------|
| 1 — Captura / preprocesado (SAM, fondo, frames de vídeo) | Media | _____ | _____ |
| **2 — Reconstrucción 3D (IA)** ⭐ | **Alta** | _____ | _____ |
| **3 — Reparación generativa (IA)** ⭐ | **Alta** | _____ | _____ |
| 4 — STL imprimible (watertight, Open3D/MeshLab) | Media | _____ | _____ |
| 5 — App / integración end-to-end | Media | _____ | _____ |

Las etapas **2 y 3 son el núcleo de IA** del TFM: conviene que tengan a las
personas con más dedicación. Encaja con el reparto **2-2-1** acordado: 2 personas
volcadas en E2, 2 en E3, 1 de "fontanería"/integración (E1, E4, E5).

> Rellenad los nombres en la reunión de reparto. Sugerencia: que el secundario de
> una etapa sea el primario de la etapa *vecina* (así las interfaces las acuerdan
> dos personas que ya se entienden).

---

## Capa 3 — Reglas que hacen que funcione

1. **Repositorio Git compartido** (GitHub). Una rama por persona/tarea; cada cambio
   entra por *pull request* revisado por el secundario de esa etapa. Ver
   `TFM_10_Guia_Git_Grupo.md`.
2. **Contratos de interfaz por escrito** (qué formato pasa de una etapa a la
   siguiente). Es lo más crítico: sin esto la integración falla aunque cada módulo
   funcione. Ver `TFM_11_Contratos_Interfaz.md`.
3. **Datos en sitio común** (Hugging Face / Drive), nunca solo en un portátil. Los
   datasets NO se suben a Git (ver `.gitignore` en la guía de Git).
4. **Sync semanal fijo** (30-45 min): qué hice / qué me bloquea / qué interfaz
   necesito de otro. Acta corta en el repo.
5. **Definición de "hecho"**: una etapa está hecha cuando produce su salida en el
   formato del contrato + tiene un test mínimo + el secundario la ha revisado.

---

## Cronograma (revisar fechas pasadas en la reunión)

| Fase | Fechas | Qué |
|------|--------|-----|
| Arranque común | 10-26 jun | Pipeline de juguete entre todos + reparto de roles |
| **Cerrar interfaces** | **lo antes posible (era 21 jun)** | Acordar contratos E1→E2 y E2→E3 |
| Desarrollo en paralelo | hasta 2 ago | Cada quien su etapa, PR revisados |
| Congelar núcleo P0 | **16 ago** | No más features nuevas en el núcleo |
| Integración | 3-16 ago | Encajar etapas (⚠️ agosto = vacaciones, planificar) |
| Evaluación | 17-30 ago | Métricas: Chamfer, IoU, imprimibilidad |
| Redacción memoria | 31 ago-12 sep | Documento final + slides |
| Buffer + entrega | 13-15 sep | Margen e imprevistos |

> Los hitos del 18 y 21 jun (presentación y cierre de interfaces) probablemente se
> hayan movido. Confirmadlos en el próximo sync y actualizad esta tabla.

---

## Primeros pasos concretos (esta semana)

- [ ] Reunión de reparto: rellenar la matriz de propiedad.
- [ ] Crear el repo de GitHub y que las 5 hagáis `clone` (ver `TFM_10`).
- [ ] Acordar y escribir los contratos de interfaz (ver `TFM_11`).
- [ ] Elegir dónde viven los datos (HF/Drive) y enlazarlo aquí.
- [ ] Fijar día y hora del sync semanal.
