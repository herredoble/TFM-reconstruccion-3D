# -*- coding: utf-8 -*-
"""
Filtra y normaliza el dataset de tazas (.glb de Objaverse) para dejarlo listo
para las etapas siguientes del pipeline.

Qué hace con cada modelo:
  1. Lo carga y, si es una escena con varias piezas, las une en una sola malla.
  2. FILTRA: descarta las mallas degeneradas (< MIN_FACES caras).
  3. SIMPLIFICA: si tiene > MAX_FACES caras, intenta reducirlas (si hay backend).
  4. NORMALIZA: centra la malla en el origen y la escala a tamaño unidad.
  5. Exporta la malla limpia a Datos/tazas_limpias/<uid>.ply

Salidas (en C:\\edf\\tfm\\):
  - Datos/tazas_limpias/<uid>.ply     -> mallas validas, normalizadas (solo geometria)
  - Datos/informe_filtrado.csv        -> que paso con cada modelo y por que

Nota: la normalizacion conserva la GEOMETRIA (forma), no la textura/color
(no hace falta para reconstruir e imprimir, que van sobre la forma).
La ORIENTACION no se corrige automaticamente (es dificil); se revisa luego si hace falta.
"""
import os, csv, glob
import trimesh

BASE = r"C:\edf\tfm"
ORIGEN = os.path.join(BASE, "Datos", "objaverse", "raw")
DESTINO = os.path.join(BASE, "Datos", "objaverse", "limpias")
INFORME = os.path.join(BASE, "Datos", "objaverse", "metadatos", "informe_filtrado.csv")

MIN_FACES = 1000        # menos que esto = degenerada -> descartar
MAX_FACES = 200000      # mas que esto = pesada -> intentar simplificar


def cargar_malla(ruta):
    """Carga un .glb y devuelve una unica malla (uniendo piezas si hace falta)."""
    cargado = trimesh.load(ruta, force="mesh")  # force=mesh intenta devolver una malla unica
    if isinstance(cargado, trimesh.Scene):
        if len(cargado.geometry) == 0:
            return None
        return trimesh.util.concatenate([g for g in cargado.geometry.values()])
    if isinstance(cargado, trimesh.Trimesh):
        return cargado
    return None


def main():
    os.makedirs(DESTINO, exist_ok=True)
    archivos = sorted(glob.glob(os.path.join(ORIGEN, "*.glb")))
    print(f"Modelos a procesar: {len(archivos)}")

    filas = []
    n_ok = n_desc = n_simpl = n_error = 0

    for ruta in archivos:
        uid = os.path.splitext(os.path.basename(ruta))[0]
        estado, caras_ini, caras_fin, watertight = "", "", "", ""
        try:
            m = cargar_malla(ruta)
            if m is None or len(m.faces) == 0:
                estado = "descartada_vacia"; n_desc += 1
                filas.append([uid, caras_ini, caras_fin, watertight, estado]); continue

            caras_ini = len(m.faces)

            # 2) Filtrar degeneradas
            if caras_ini < MIN_FACES:
                estado = "descartada_pocas_caras"; n_desc += 1
                filas.append([uid, caras_ini, caras_fin, watertight, estado]); continue

            # 3) Simplificar las muy pesadas (con fallback si no hay backend)
            if caras_ini > MAX_FACES:
                try:
                    m = m.simplify_quadric_decimation(face_count=MAX_FACES)
                    estado = "simplificada"; n_simpl += 1
                except Exception:
                    estado = "ok_pesada_sin_simplificar"
            else:
                estado = "ok"

            # 4) Normalizar: centrar en el origen y escalar a tamano unidad
            m.apply_translation(-m.centroid)
            ext = max(m.extents) if max(m.extents) > 0 else 1.0
            m.apply_scale(1.0 / ext)

            caras_fin = len(m.faces)
            watertight = m.is_watertight

            # 5) Exportar geometria limpia
            m.export(os.path.join(DESTINO, uid + ".ply"))
            if estado in ("ok", "ok_pesada_sin_simplificar", "simplificada"):
                n_ok += 1
            filas.append([uid, caras_ini, caras_fin, watertight, estado])

        except Exception as e:
            estado = f"error: {type(e).__name__}"; n_error += 1
            filas.append([uid, caras_ini, caras_fin, watertight, estado])

    # Guardar informe
    with open(INFORME, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid", "caras_originales", "caras_finales", "watertight", "estado"])
        w.writerows(filas)

    print("=== RESUMEN ===")
    print(f"Validas (guardadas): {n_ok}")
    print(f"  - de ellas, simplificadas: {n_simpl}")
    print(f"Descartadas: {n_desc}")
    print(f"Errores: {n_error}")
    print(f"Dataset limpio en: {DESTINO}")
    print(f"Informe en: {INFORME}")


if __name__ == "__main__":
    main()
