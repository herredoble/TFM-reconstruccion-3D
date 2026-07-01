# TFM — Reconstrucción y reparación 3D de objetos a partir de imágenes o vídeo

> Raquel Roca · Junio 2026 · Grupo de 5 personas · Entrega: 15 sep 2026

---

## Objetivo

Dado un objeto entero o roto fotografiado o grabado en vídeo, generar automáticamente un modelo 3D reparado y listo para imprimir en formato `.STL`.

El elemento diferenciador frente a un escáner 3D convencional es la **reparación automática mediante IA** de las partes dañadas o que faltan. Caso de uso: se rompe una pieza de cerámica (taza, cuenco, jarrón), el usuario la fotografía o la graba, el sistema reconstruye su forma original y genera el archivo para reimprimir la pieza.

---

## Núcleo del proyecto: etapas 2 y 3

### Etapa 2 — Reconstrucción 3D (imágenes → malla de puntos)

A partir de un conjunto de imágenes del objeto (o frames extraídos automáticamente de un vídeo), el modelo genera una nube de puntos y malla 3D que representa su geometría.

El foco de investigación está en aprender este mapeo con deep learning (NeRF, Gaussian Splatting o modelos image-to-3D como Zero123/LRM) para que funcione con pocas imágenes y sin calibración de cámara manual.

### Etapa 3 — Reparación IA (malla rota → malla completa)

La malla obtenida en la etapa anterior puede estar incompleta: el objeto estaba roto, o la reconstrucción tiene huecos. Un modelo generativo de shape completion rellena las partes que faltan y devuelve la geometría completa, lista para exportar a `.STL` imprimible.

Ambas etapas se entrenan sobre la super-categoría **vasijas** (taza, cuenco, jarrón, vaso): misma topología, ~700 modelos en Objaverse, fotos reales en CO3D, roturas reales en Fantastic Breaks.

---

## Modos de entrada previstos

- **P0 — imágenes JPG con fondo blanco:** entrada controlada, máxima simplicidad. Permite centrarse en las etapas 2 y 3 sin depender de una etapa 1 compleja.
- **P1 — imágenes con fondo real:** el sistema elimina el fondo automáticamente (SAM) e incluye un módulo que evalúa si las imágenes son suficientes en número, ángulo y calidad antes de intentar reconstruir. Si no lo son, avisa al usuario.
- **P1/P2 — entrada por vídeo:** el usuario graba el objeto girando y el sistema extrae automáticamente los frames más útiles (variedad angular, nitidez, sin duplicados).

---

## Lo que se entrega (P0)

Pipeline completo y funcional de punta a punta sobre la categoría vasijas:

- Etapas 2 y 3 desarrolladas e investigadas por el equipo.
- Etapas 1 y 4 resueltas con herramientas existentes (SAM + COLMAP; Open3D/MeshLab).
- Demo: foto de taza (entera o rota) → `.STL` listo para laminador.
- Métricas cuantitativas: distancia de Chamfer (reconstrucción), IoU (reparación), test de imprimibilidad.

---

## Dificultades pendientes

- **Brecha render–foto real:** el modelo entrena con imágenes sintéticas; puede degradarse con fotos de móvil reales. Requiere data augmentation y validación con CO3D.
- **Evaluación automática de suficiencia de imágenes:** definir cuándo hay bastantes vistas para reconstruir bien es un problema abierto; solución provisional: umbral empírico de cobertura angular.
- **Extracción inteligente de frames de vídeo:** seleccionar automáticamente los frames más informativos (sin duplicados, cobertura angular suficiente) requiere una heurística o un clasificador adicional.
- **Generalización a tipos de daño no vistos:** el modelo de reparación puede fallar con roturas muy distintas a las del entrenamiento sintético; Fantastic Breaks como validación real mitiga pero no elimina este riesgo.
