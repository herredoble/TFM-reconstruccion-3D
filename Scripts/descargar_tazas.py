# -*- coding: utf-8 -*-
"""
Descarga COMPLETA de los datos de tazas para el TFM, con toda la metainformacion.

Qué hace:
  1. Reúne TODOS los modelos de tazas de Objaverse (mug, cup, teacup, measuring_cup, Dixie_cup).
  2. Descarga sus metadatos (nombre, descripción, tags, licencia, autor, nº de caras/vértices...).
  3. Guarda los metadatos en CSV (resumen) y JSON (completo).
  4. Descarga los modelos .glb y los copia a Datos/tazas_objaverse/.

Salidas (dentro del proyecto C:\\edf\\tfm\\):
  - Datos/tazas_objaverse/<uid>.glb            -> los modelos 3D
  - Datos/metadatos_tazas.csv                  -> tabla resumen (Excel-friendly)
  - Datos/metadatos_tazas_completo.json        -> metadatos crudos completos
  - Datos/tazas_por_categoria.json             -> qué uids hay en cada categoría

Otras BBDD del proyecto (no se bajan aquí; ver notas al final):
  - Fantastic Breaks (roturas reales), Thingi10K (imprimibilidad), CO3D (fotos reales), ShapeNet (mug 03797390).
"""
import os, csv, json
import objaverse

# --- Configuración ---
BASE = r"C:\edf\tfm"
DATOS = os.path.join(BASE, "Datos")
DEST_GLB = os.path.join(DATOS, "tazas_objaverse")
CATEGORIAS = ["mug", "cup", "teacup", "measuring_cup", "Dixie_cup"]  # ajustable


def main():
    os.makedirs(DEST_GLB, exist_ok=True)

    # 1) Reunir uids de todas las categorías de taza
    lvis = objaverse.load_lvis_annotations()
    por_categoria = {c: lvis.get(c, []) for c in CATEGORIAS}
    uids = sorted({u for lista in por_categoria.values() for u in lista})
    print(f"Categorías: {CATEGORIAS}")
    print(f"Total tazas únicas: {len(uids)}")

    with open(os.path.join(DATOS, "tazas_por_categoria.json"), "w", encoding="utf-8") as f:
        json.dump(por_categoria, f, ensure_ascii=False, indent=2)

    # 2) Descargar metadatos (toda la info disponible de cada objeto)
    print("Descargando metadatos...")
    anotaciones = objaverse.load_annotations(uids)   # {uid: dict con toda la info}

    # 3a) Guardar metadatos crudos completos (JSON)
    with open(os.path.join(DATOS, "metadatos_tazas_completo.json"), "w", encoding="utf-8") as f:
        json.dump(anotaciones, f, ensure_ascii=False, indent=2)

    # 3b) Guardar resumen legible (CSV)
    cat_de = {u: [c for c in CATEGORIAS if u in set(por_categoria[c])] for u in uids}
    columnas = ["uid", "nombre", "categorias_lvis", "tags", "licencia", "autor",
                "vertices", "caras", "animaciones", "url"]
    with open(os.path.join(DATOS, "metadatos_tazas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        for u in uids:
            a = anotaciones.get(u, {}) or {}
            tags = ",".join(t.get("name", "") for t in a.get("tags", []) if isinstance(t, dict))
            licencia = a.get("license", "")
            autor = ""
            if isinstance(a.get("user"), dict):
                autor = a["user"].get("displayName") or a["user"].get("username", "")
            w.writerow([
                u,
                a.get("name", ""),
                "|".join(cat_de[u]),
                tags,
                licencia,
                autor,
                a.get("vertexCount", ""),
                a.get("faceCount", ""),
                a.get("animationCount", ""),
                a.get("viewerUrl", a.get("uri", "")),
            ])
    print("Metadatos guardados: metadatos_tazas.csv y metadatos_tazas_completo.json")

    # 4) Descargar los modelos .glb y copiarlos al proyecto
    print("Descargando modelos .glb (esto tarda)...")
    objetos = objaverse.load_objects(uids=uids, download_processes=1)   # {uid: ruta_cache}
    import shutil
    copiados = 0
    for uid, ruta in objetos.items():
        try:
            shutil.copy(ruta, os.path.join(DEST_GLB, uid + ".glb"))
            copiados += 1
        except Exception as e:
            print("  (no se pudo copiar", uid, ":", e, ")")
    print(f"Modelos copiados a {DEST_GLB}: {copiados}")
    print("=== LISTO ===")


if __name__ == "__main__":
    main()
