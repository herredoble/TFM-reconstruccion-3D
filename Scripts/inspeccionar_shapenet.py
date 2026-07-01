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
import argparse

REPO_ID = "ShapeNet/ShapeNetCore"
REPO_TYPE = "dataset"

# Synsets (IDs WordNet) de la super-categoria VASIJAS para el TFM.
VASIJAS = {
    "03797390": "mug (taza)",
    "02880940": "bowl (cuenco)",
    "02876657": "bottle (botella)",
    "03593526": "jar (jarra/tarro)",
    "02946921": "can (lata)",
    "03991062": "flowerpot (maceta)",
    "02747177": "trash bin (cubo)",
}

BASE = r"C:\edf\tfm"
DEST = os.path.join(BASE, "Datos", "shapenet", "raw")


def _token():
    """Devuelve el token de HF: primero env var, luego cache de hf auth login."""
    tok = os.environ.get("HF_TOKEN")
    if tok:
        return tok
    try:
        from huggingface_hub import get_token
        return get_token()
    except Exception:
        return None


def listar_ficheros_repo():
    """Imprime los ficheros del repo de HF para ver los nombres exactos."""
    from huggingface_hub import list_repo_files
    ficheros = list(list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE, token=_token()))
    print(f"\nFicheros en {REPO_ID} ({len(ficheros)}):")
    for f in sorted(ficheros):
        print("  ", f)
    return ficheros


def resumen_repo():
    """Lista los synsets disponibles en el repo y resalta los de vasijas."""
    from huggingface_hub import list_repo_files
    ficheros = list(list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE, token=_token()))
    zips = sorted(f.replace(".zip", "") for f in ficheros if f.endswith(".zip"))

    print(f"\nShapeNet/ShapeNetCore — {len(zips)} categorias disponibles")
    print("-" * 50)
    for sid in zips:
        marca = f"  <== {VASIJAS[sid]}" if sid in VASIJAS else ""
        print(f"  {sid}{marca}")
    print("-" * 50)

    print("\n=== Vasijas del TFM ===")
    for sid, etiqueta in VASIJAS.items():
        encontrado = f"{sid}.zip" in ficheros
        estado = "OK — disponible" if encontrado else "NO encontrado en el repo"
        print(f"  {sid}  {etiqueta:<18}  {estado}")
    print()
    print("Para descargar: python Scripts/inspeccionar_shapenet.py --descargar")


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
        print("AVISO: no se encontró token de HF. Ejecuta 'hf auth login' o define HF_TOKEN.\n")

    if args.listar:
        listar_ficheros_repo()
    else:
        resumen_repo()

    if args.descargar:
        descargar_vasijas()


if __name__ == "__main__":
    main()
