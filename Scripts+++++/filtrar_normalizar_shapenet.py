# -*- coding: utf-8 -*-
"""
Filtra y normaliza el dataset de vasijas (.obj de ShapeNet) para dejarlo
listo para las etapas siguientes del pipeline.

Qué hace con cada modelo:
  1. Localiza model_normalized.obj dentro de la carpeta del modelo.
  2. Lo carga y, si es una escena con varias piezas, las une en una sola malla.
  3. FILTRA: descarta las mallas degeneradas (< MIN_FACES caras).
  4. SIMPLIFICA: si tiene > MAX_FACES caras, intenta reducirlas.
  5. NORMALIZA: centra en el origen y escala a tamaño unidad.
  6. Exporta a Datos/shapenet/limpias/<synset>/<model_id>.ply

Salidas:
  - Datos/shapenet/limpias/<synset>/<model_id>.ply  -> mallas limpias/normalizadas
  - Datos/shapenet/metadatos/informe_filtrado.csv   -> qué pasó con cada modelo

Estructura de entrada esperada:
  Datos/shapenet/raw/<synset>/<synset>/<model_id>/**/model_normalized.obj
"""
import os
import csv
import glob
import trimesh

BASE = r"C:\edf\tfm"
ORIGEN  = os.path.join(BASE, "Datos", "shapenet", "raw")
DESTINO = os.path.join(BASE, "Datos", "shapenet", "limpias")
INFORME = os.path.join(BASE, "Datos", "shapenet", "metadatos", "informe_filtrado.csv")

VASIJAS = {
    "03797390": "mug",
    "02880940": "bowl",
    "02876657": "bottle",
    "03593526": "jar",
    "02946921": "can",
    "03991062": "flowerpot",
    "02747177": "trash_bin",
}

MIN_FACES = 1000
MAX_FACES = 200_000


def encontrar_obj(model_dir):
    """Devuelve la ruta del model_normalized.obj dentro de la carpeta del modelo."""
    for ruta in glob.glob(os.path.join(model_dir, "**", "model_normalized.obj"), recursive=True):
        return ruta
    return None


def cargar_malla(ruta_obj):
    """Carga un .obj y devuelve una única malla (uniendo piezas si hace falta)."""
    cargado = trimesh.load(ruta_obj, force="mesh")
    if isinstance(cargado, trimesh.Scene):
        if not cargado.geometry:
            return None
        return trimesh.util.concatenate(list(cargado.geometry.values()))
    if isinstance(cargado, trimesh.Trimesh):
        return cargado
    return None


def main():
    os.makedirs(DESTINO, exist_ok=True)
    os.makedirs(os.path.dirname(INFORME), exist_ok=True)

    filas = []
    n_ok = n_desc = n_simpl = n_error = 0
    total_procesados = 0

    for synset_id, categoria in VASIJAS.items():
        synset_dir = os.path.join(ORIGEN, synset_id, synset_id)
        if not os.path.isdir(synset_dir):
            print(f"[AVISO] No encontrado: {synset_dir}")
            continue

        model_ids = sorted(
            d for d in os.listdir(synset_dir)
            if os.path.isdir(os.path.join(synset_dir, d))
        )
        print(f"\n--- {categoria} ({synset_id}): {len(model_ids)} modelos ---")

        dest_synset = os.path.join(DESTINO, synset_id)
        os.makedirs(dest_synset, exist_ok=True)

        for model_id in model_ids:
            model_dir = os.path.join(synset_dir, model_id)
            ruta_obj = encontrar_obj(model_dir)
            caras_ini = caras_fin = watertight = estado = ""
            total_procesados += 1

            if ruta_obj is None:
                estado = "sin_obj"
                n_error += 1
                filas.append([synset_id, categoria, model_id, caras_ini, caras_fin, watertight, estado])
                continue

            try:
                m = cargar_malla(ruta_obj)

                if m is None or len(m.faces) == 0:
                    estado = "descartada_vacia"
                    n_desc += 1
                    filas.append([synset_id, categoria, model_id, caras_ini, caras_fin, watertight, estado])
                    continue

                caras_ini = len(m.faces)

                if caras_ini < MIN_FACES:
                    estado = "descartada_pocas_caras"
                    n_desc += 1
                    filas.append([synset_id, categoria, model_id, caras_ini, caras_fin, watertight, estado])
                    continue

                if caras_ini > MAX_FACES:
                    try:
                        m = m.simplify_quadric_decimation(face_count=MAX_FACES)
                        estado = "simplificada"
                        n_simpl += 1
                    except Exception:
                        estado = "ok_pesada_sin_simplificar"
                else:
                    estado = "ok"

                m.apply_translation(-m.centroid)
                ext = max(m.extents) if max(m.extents) > 0 else 1.0
                m.apply_scale(1.0 / ext)

                caras_fin = len(m.faces)
                watertight = m.is_watertight

                m.export(os.path.join(dest_synset, model_id + ".ply"))
                if estado in ("ok", "ok_pesada_sin_simplificar", "simplificada"):
                    n_ok += 1

            except Exception as e:
                estado = f"error: {type(e).__name__}"
                n_error += 1

            filas.append([synset_id, categoria, model_id, caras_ini, caras_fin, watertight, estado])

            if total_procesados % 100 == 0:
                print(f"  {total_procesados} procesados hasta ahora...")

    with open(INFORME, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["synset_id", "categoria", "model_id", "caras_originales", "caras_finales", "watertight", "estado"])
        w.writerows(filas)

    print("\n=== RESUMEN ===")
    print(f"Total procesados : {total_procesados}")
    print(f"Válidos guardados: {n_ok}  (de ellos simplificados: {n_simpl})")
    print(f"Descartados      : {n_desc}")
    print(f"Errores          : {n_error}")
    print(f"Dataset limpio en: {DESTINO}")
    print(f"Informe en       : {INFORME}")


if __name__ == "__main__":
    main()
