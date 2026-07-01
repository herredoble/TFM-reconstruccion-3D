# -*- coding: utf-8 -*-
"""
Inspecciona ShapeNetCore desde el mirror OFICIAL de Hugging Face
(https://huggingface.co/datasets/ShapeNet/ShapeNetCore) SIN descargar los 51K modelos.

Por qué este script:
  La web shapenet.org casi nunca funciona (login y visor rotos). Tener el acceso
  aprobado ahí solo sirve para una cosa: aceptar los términos. Los datos reales se
  navegan y descargan desde el mirror de Hugging Face.

Qué hace:
  1. Lista los ficheros que contiene el repo de HF (para ver nombres exactos).
  2. Descarga SOLO taxonomy.json (pequeño) y lista las categorías con su nº de modelos.
  3. Resalta los synsets de VASIJAS que nos interesan (mug, bowl, bottle, jar).
  4. (Opcional) Descarga solo los .zip de los synsets de vasijas, no el dataset entero.

Requisitos:
  pip install huggingface_hub
  - Cuenta de Hugging Face con los términos de ShapeNetCore aceptados:
    https://huggingface.co/datasets/ShapeNet/ShapeNetCore  -> botón "Agree and access"
    (usa el mismo email con el que pediste acceso a shapenet.org).
  - Token de HF: https://huggingface.co/settings/tokens  (tipo "read")
    Ponlo en la variable de entorno HF_TOKEN, o ejecuta antes:  huggingface-cli login

Uso (desde C:\\edf\\tfm):
  python Scripts/inspeccionar_shapenet.py                 # inspecciona (taxonomy + categorías)
  python Scripts/inspeccionar_shapenet.py --listar        # lista los ficheros del repo
  python Scripts/inspeccionar_shapenet.py --descargar     # además baja los synsets de vasijas
"""
import os
import json
import argparse

REPO_ID = "ShapeNet/ShapeNetCore"
REPO_TYPE = "dataset"

# Synsets (IDs WordNet) de la super-categoria VASIJAS para el TFM.
VASIJAS = {
    "03797390": "mug (taza)",
    "02880940": "bowl (cuenco)",
    "02876657": "bottle (botella)",
    "03593526": "jar (jarra/tarro)",
}

BASE = r"C:\edf\tfm"
DEST = os.path.join(BASE, "Datos", "shapenet_vasijas")


def _token():
    return os.environ.get("HF_TOKEN")


def listar_ficheros_repo():
    """Imprime los ficheros del repo de HF para ver los nombres exactos."""
    from huggingface_hub import list_repo_files
    ficheros = list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE, token=_token())
    print(f"\nFicheros en {REPO_ID} ({len(ficheros)}):")
    for f in sorted(ficheros):
        print("  ", f)
    return ficheros


def cargar_taxonomia():
    """Descarga SOLO taxonomy.json y lo devuelve parseado."""
    from huggingface_hub import hf_hub_download
    ruta = hf_hub_download(
        repo_id=REPO_ID, repo_type=REPO_TYPE,
        filename="taxonomy.json", token=_token(),
    )
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_categorias(taxonomia):
    """taxonomy.json es una lista de nodos {synsetId, name, numInstances, children}."""
    filas = []
    for nodo in taxonomia:
        sid = nodo.get("synsetId", "")
        nombre = nodo.get("name", "")
        n = nodo.get("numInstances", 0)
        filas.append((n, sid, nombre))
    filas.sort(reverse=True)

    print(f"\n{'N':>7}  {'synsetId':<10}  categoria")
    print("-" * 64)
    for n, sid, nombre in filas:
        marca = "   <== VASIJA" if sid in VASIJAS else ""
        print(f"{n:>7}  {sid:<10}  {nombre[:38]}{marca}")
    print("-" * 64)
    print(f"Total categorias: {len(filas)}  ·  Total modelos: {sum(f[0] for f in filas)}")

    print("\n=== Resumen VASIJAS ===")
    for sid, etiqueta in VASIJAS.items():
        match = next((f for f in filas if f[1] == sid), None)
        n = match[0] if match else "NO ENCONTRADO en taxonomy"
        print(f"  {sid}  {etiqueta:<18}  -> {n} modelos")


def descargar_vasijas():
    """Descarga solo los .zip de los synsets de vasijas (no el dataset entero)."""
    from huggingface_hub import hf_hub_download
    os.makedirs(DEST, exist_ok=True)
    for sid, etiqueta in VASIJAS.items():
        print(f"Descargando {sid} ({etiqueta}) ...")
        try:
            ruta = hf_hub_download(
                repo_id=REPO_ID, repo_type=REPO_TYPE,
                filename=f"{sid}.zip", token=_token(), local_dir=DEST,
            )
            print(f"  OK -> {ruta}")
        except Exception as e:
            print(f"  (no se pudo bajar {sid}.zip: {e})")
            print("   -> usa --listar para ver el nombre exacto del fichero en el repo.")
    print("\n=== LISTO ===  Descomprime los .zip dentro de", DEST)


def main():
    ap = argparse.ArgumentParser(description="Inspecciona ShapeNetCore desde Hugging Face.")
    ap.add_argument("--listar", action="store_true", help="Lista los ficheros del repo de HF.")
    ap.add_argument("--descargar", action="store_true", help="Baja los synsets de vasijas.")
    args = ap.parse_args()

    if not _token():
        print("AVISO: no hay HF_TOKEN en el entorno. Como el dataset es 'gated', "
              "ejecuta antes 'huggingface-cli login' o define HF_TOKEN.\n")

    if args.listar:
        listar_ficheros_repo()

    try:
        taxonomia = cargar_taxonomia()
        listar_categorias(taxonomia)
    except Exception as e:
        print(f"\nNo se pudo cargar taxonomy.json: {e}")
        print("Comprueba: (1) términos aceptados en la web del dataset, (2) token válido.")
        print("Ejecuta con --listar para ver qué ficheros hay realmente en el repo.")

    if args.descargar:
        descargar_vasijas()


if __name__ == "__main__":
    main()
