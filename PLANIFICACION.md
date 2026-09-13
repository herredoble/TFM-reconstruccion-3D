# Planificación TFM — estado final a entrega

> Raquel Roca · última actualización: 13 sep 2026 (1 día antes de la entrega)
> Entrega: **15 septiembre 2026**

---

## Estado final del pipeline — COMPLETO ✅

```
[Fotos] → E2 (Pix2Vox++) → [Nube rota (2048,3)] → E3 (PoinTr) → [Nube completa]
       → E4 (Poisson) → [STL watertight] → APP+++++ (Gradio REBUILD3D)
```

**Mejor resultado E3:** PoinTr v6_obj_sn · CD = 0.0245 · F-Score = 0.4547 · época 486/500  
**Demo funcional:** fotos reales de tazas rotas → STL imprimible (E5 + Gradio app)

---

## Hitos completados

### Raquel — E3 datos + pipeline + memoria

| Tarea | Fecha | Resultado |
|-------|-------|-----------|
| Preprocesado Fantastic Breaks | 11 jul 2026 | 61 pares vasija, 2.048 pts |
| Subir datos a Drive | 11 jul 2026 | shapenet_limpias/ + objaverse_limpias/ + FB procesado |
| Generación roturas sintéticas v1 | ago 2026 | 2.299 pares (plano+chip+cuña) |
| Data loader PyTorch E3 | ago 2026 | dataset.py + train.py + evaluate.py |
| PCN v3 entrenado | ago 2026 | CD=0.0665, F=0.024, A100 |
| Roturas sintéticas v2 | ago 2026 | plano+chip+cuña mejorado |
| PCN v4 entrenado | ago 2026 | CD=0.0641, F=0.0236, época 480 |
| PCN v5 entrenado | ago 2026 | CD=0.0630, F=0.0257, época 445 (fix centroide) |
| PoinTr v1 → v4 | ago 2026 | iteraciones de mejora de datos y arquitectura |
| PoinTr v5_obj | ago 2026 | CD=0.0306, F=0.270, época 490 |
| **PoinTr v6_obj_sn** | **27 ago 2026** | **CD=0.0245, F=0.4547 — MEJOR RESULTADO** |
| PoinTr v7 fine-tune (FB) | sep 2026 | fine-tuning con Fantastic Breaks |
| E4 pipeline STL | 6 sep 2026 | Poisson depth=7–10, 6 objetos validados |
| convertir_voxels_a_nube.py | 6 sep 2026 | conversión E2→E3 (voxel 32³ → nube 2048,3) |
| E5 app_pipeline_demo.ipynb | 6 sep 2026 | pipeline E2→E3→E4 + Gradio |
| Secciones memoria TFM | 6 sep 2026 | sec.6 E3 + sec.7 E4 redactadas |
| memoria_tfm.tex completo | 11 sep 2026 | LaTeX/Overleaf + referencias.bib (19 entradas) |
| APP+++++ Gradio REBUILD3D | 12 sep 2026 | demo con fotos reales de tazas, 5 ángulos fijos |
| Reorganización GitHub | 13 sep 2026 | +++++  repo limpio, PR a main, README actualizado |

### E2 — Álvaro + Almu (Pix2Vox++)

| Tarea | Fecha | Resultado |
|-------|-------|-----------|
| Método elegido: Pix2Vox++ | 25 jul 2026 | multi-vista → voxel grid 32³ |
| Imágenes sintéticas (5 vistas) | ago 2026 | 20 categorías ShapeNet |
| Fine-tuning con tazas rotas | ago 2026 | mejor generalización con tazas |
| Evaluación con tazas rotas reales | sep 2026 | exp14 mejor resultado |
| E1 simplificado | sep 2026 | 5 ángulos fijos + alpha compositing (sin SAM/COLMAP) |
| Interfaz E2→E3 resuelta | 6 sep 2026 | voxel 32³ → nube (2048,3) con FPS |

### Grupo — integración y entrega

| Tarea | Fecha | Estado |
|-------|-------|--------|
| Contrato E2→E3 cerrado | 6 sep 2026 | ✅ numpy float32 (2048,3) centrado |
| Pipeline end-to-end funcional | 12 sep 2026 | ✅ demo con fotos reales |
| Repo GitHub limpio | 13 sep 2026 | ✅ PR raquel/e3 → main mergeado |
| Memoria LaTeX | 13 sep 2026 | ✅ en Overleaf, secciones completas |

---

## Reparto del equipo — estado final

| Persona | Etapa | Estado |
|---------|-------|--------|
| **Álvaro** | E2 arquitectura Pix2Vox++ | ✅ Fine-tuning tazas rotas completo |
| **Almu** | E1+E2 implementación | ✅ Pipeline fotos → voxels funcional |
| **Luis** | E2 métricas + integración | ✅ Chamfer Distance y F-Score implementados |
| **Rocío** | E3 modelo (roturas centradas) | ✅ generar_roturas_centradas.ipynb integrado |
| **Raquel** | E3 datos + pipeline + memoria | ✅ PoinTr v6 (CD=0.0245) + LaTeX + repo |

---

## Datasets — estado final

| Dataset | Estado | Uso |
|---------|--------|-----|
| ShapeNet (mug+bowl+bottle+jar+can) | ✅ 2.170 modelos .ply | E2+E3 entrenamiento |
| Objaverse (vasijas) | ✅ 197 modelos .ply | E2+E3 complemento |
| Fantastic Breaks | ✅ 61 pares vasija (2.048 pts) | E3 fine-tuning |
| Roturas sintéticas | ✅ 2.299 pares generados | E3 entrenamiento |
| CO3D | Pospuesto a P1 | — |

Los datos viven en Drive (no en Git). Scripts de descarga en `Scripts+++++/`.

---

## Cronograma ejecutado

| Periodo | Hito | Estado |
|---------|------|--------|
| Jul 2026 | Datos preprocesados, contratos E2↔E3, arranque modelos | ✅ |
| Ago 2026 | E2 Pix2Vox++ entrenado, E3 PCN+PoinTr iteraciones, E4 STL | ✅ |
| 1-13 sep 2026 | PoinTr v6 BEST, E5 app, memoria LaTeX, repo limpio | ✅ |
| **15 sep 2026** | **Entrega** | ⬅ mañana |
