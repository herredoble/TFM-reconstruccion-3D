# Contexto del proyecto para Claude Code

> Este archivo lo lee Claude Code automáticamente al abrirse en esta carpeta.
> Da contexto completo del TFM a cualquier miembro del grupo que lo use.

---

## Qué es este proyecto

TFM de grupo (5 personas, máster IA/Data Science). Pipeline completo de
**reconstrucción y reparación 3D**: fotos de un objeto roto → archivo STL imprimible.

**Entrega:** 15 de septiembre de 2026.
**Repo:** https://github.com/herredoble/TFM-reconstruccion-3D

---

## Las 5 etapas del pipeline

```
[Fotos] → E1 → [PNGs recortados + poses] → E2 → [Nube de puntos rota, .npy (2048,3)]
       → E3 → [Malla completa .obj] → E4 → [STL watertight] → E5 → [App Gradio]
```

- **E1** Captura: SAM (fondo), COLMAP (poses de cámara)
- **E2** Reconstrucción: nerfacto (NeRF) o Zero123 — Álvaro decide esta semana
- **E3** Reparación: shape completion con PoinTr / PCN / SnowFlakeNet — Rocío
- **E4** STL imprimible: Open3D / MeshLab — watertight y normalizado
- **E5** App end-to-end: Gradio

El núcleo de IA es **E2 + E3**. E1, E4 y E5 usan herramientas existentes.

---

## Reparto del equipo

| Persona | Etapa principal | Primera tarea |
|---------|----------------|---------------|
| Álvaro  | E2 arquitectura | Decidir nerfacto vs Zero123 (urgente, desbloquea al grupo) |
| Almu    | E1 + E2 implementación | Pipeline de juguete: fotos sintéticas de una taza → nube de puntos |
| Luis    | E2 métricas + integración E2→E3 | Implementar Chamfer Distance y F-Score |
| Rocío   | E3 modelo | Elegir baseline (PCN recomendado), primer entrenamiento |
| Raquel  | E3 datos | Datos listos — ver estado en PLANIFICACION.md |

---

## Estado de los datos (12 jul 2026)

| Dataset | Estado | Dónde |
|---------|--------|-------|
| ShapeNet 2.170 modelos .ply | ✅ Listo | Drive → `shapenet_limpias/` |
| Objaverse 197 modelos .ply | ✅ Listo | Drive → `objaverse_limpias/` |
| Fantastic Breaks 61 pares .npy (2048 pts) | ✅ Listo | Drive → `fantastic_breaks_procesado/` |
| CO3D (fotos reales) | Pospuesto a P1 | — |
| ModelNet40 | Pendiente | — |

Los datos viven en Drive (no en Git — `Datos/` está en `.gitignore`).

---

## Contratos de interfaz (formato de salida de cada etapa)

- **E1 → E2:** N PNGs recortados + `cameras.json` (intrínsecas + extrínsecas)
- **E2 → E3:** numpy float32, shape `(2048, 3)`, centrado en origen, escala esfera unidad
- **E3 → E4:** malla completa `.obj` o `.ply`, sin huecos grandes
- **E4 → E5:** `.STL` watertight + `report.json` con validación

Ver `Documentacion/TFM_11_Contratos_Interfaz.md` para el detalle completo.

---

## Documentos clave

| Archivo | Para qué |
|---------|----------|
| `PLANIFICACION.md` | Estado de tareas — actualizar aquí cuando terminas algo |
| `NOTAS_Y_HALLAZGOS.md` | Bitácora técnica — añadir aquí resultados, bugs, decisiones |
| `Documentacion/TFM_11_Contratos_Interfaz.md` | Contratos entre etapas |
| `Documentacion/TFM_12_Datos_E3_Rocio.md` | Datos de entrenamiento para E3 |
| `Documentacion/TFM_13_Arranque_Grupo.md` | Guía completa de arranque para todo el grupo |

---

## Convenciones del proyecto

- **Lenguaje:** Python 3.14, trimesh (no open3d — no tiene build para 3.14)
- **Puntos por nube:** 2.048 (estándar PoinTr/PCN); regenerable con `--n_puntos` si el modelo necesita otro
- **Normalización:** centrado en origen, escala esfera unidad (radio máximo = 1)
- **Categoría:** vasijas (mug, bowl, jar, cup, bottle, can)
- **Git:** nadie escribe directo en `main`; todo cambio por rama + PR
- **Datos:** nunca en Git, siempre en Drive; los scripts de descarga están en `Scripts/`
- **Commits:** prefijo de etapa → `"E3: primer entrenamiento PCN, loss 0.12"`

---

## Cómo ayudar con este proyecto

Cuando alguien del grupo te use, lee primero `PLANIFICACION.md` para saber el
estado actual. Si te dicen que terminaron algo, actualiza `PLANIFICACION.md`
(marca como hecho) y añade el resultado a `NOTAS_Y_HALLAZGOS.md`. Luego haz
commit con el prefijo de etapa correspondiente.

Si hay un error técnico, busca primero en `NOTAS_Y_HALLAZGOS.md` — puede que
ya esté documentado (hallazgos H1-H11).
