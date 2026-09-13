# -*- coding: utf-8 -*-
"""
Descarga el dataset Fantastic Breaks (CVPR 2023) desde Google Drive.

Fantastic Breaks:
  150 objetos reales rotos emparejados con su versión completa (escaneos 3D).
  Clases: mugs, cups, bowls, jars, plates, statues, coasters, boxes, misc.
  Formato: PLY binario con color RGB.
  Cada objeto tiene:
    model_c.ply              -> versión COMPLETA (ground truth para E3)
    model_b_N_fragment_M.ply -> fragmentos ROTOS (entrada al pipeline)
    model_r_N_fragment_M.ply -> fragmentos de REPARACIÓN (proxy sintético)
  Licencia: no-exclusiva, solo investigación.
  Paper: https://arxiv.org/abs/2303.14152 (CVPR 2023)

Salidas:
  Datos/fantastic_breaks/Fantastic_Breaks_v1.zip  -> archivo descargado
  Datos/fantastic_breaks/                          -> contenido descomprimido

Uso:
  pip install gdown
  python Scripts/descargar_fantastic_breaks.py
  python Scripts/descargar_fantastic_breaks.py --solo-zip   # solo descarga, no descomprime
"""
import os
import zipfile
import argparse
from pathlib import Path

GDRIVE_FOLDER = "https://drive.google.com/drive/folders/1mGldCURVSN77ZKYfvnEYl4l-QPJRgsJK"
ZIP_NAME      = "Fantastic_Breaks_v1.zip"
BASE          = Path(r"C:\edf\tfm")
DESTINO       = BASE / "Datos" / "fantastic_breaks"


def descargar():
    try:
        import gdown
    except ImportError:
        print("Instalando gdown...")
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gdown"], check=True)
        import gdown

    DESTINO.mkdir(parents=True, exist_ok=True)
    zip_path = DESTINO / ZIP_NAME

    if zip_path.exists():
        print(f"[OK] ZIP ya existe: {zip_path}  ({zip_path.stat().st_size / 1e9:.2f} GB)")
        return zip_path

    print(f"Descargando carpeta Google Drive -> {DESTINO}")
    print("Tamaño: ~8.24 GB — puede tardar varios minutos según la conexión.")
    print()

    # Descarga la carpeta entera (contiene solo el ZIP)
    gdown.download_folder(
        url=GDRIVE_FOLDER,
        output=str(DESTINO),
        quiet=False,
        use_cookies=False,
    )

    # Buscar el zip descargado (gdown puede poner el archivo directamente)
    if zip_path.exists():
        print(f"\n[OK] Descargado: {zip_path}")
        return zip_path

    # Fallback: buscar cualquier .zip en DESTINO
    zips = list(DESTINO.glob("*.zip"))
    if zips:
        print(f"\n[OK] Descargado: {zips[0]}")
        return zips[0]

    print("\n[AVISO] No se encontró el ZIP tras la descarga.")
    print("Descarga manual: abre este enlace en el navegador y guarda en", DESTINO)
    print(" ", GDRIVE_FOLDER)
    return None


def descomprimir(zip_path):
    print(f"\nDescomprimiendo {zip_path.name} ({zip_path.stat().st_size / 1e9:.2f} GB)...")
    with zipfile.ZipFile(zip_path, "r") as z:
        total = len(z.namelist())
        print(f"  {total} archivos en el ZIP")
        z.extractall(DESTINO)
    print(f"[OK] Descomprimido en {DESTINO}")


def resumen():
    print("\n=== RESUMEN ===")
    ply_completos  = list(DESTINO.rglob("model_c.ply"))
    ply_rotos      = list(DESTINO.rglob("model_b_*.ply"))
    ply_reparacion = list(DESTINO.rglob("model_r_*.ply"))
    print(f"Objetos completos  (model_c):      {len(ply_completos)}")
    print(f"Fragmentos rotos   (model_b_*):    {len(ply_rotos)}")
    print(f"Fragmentos reparo  (model_r_*):    {len(ply_reparacion)}")
    print(f"Directorio:        {DESTINO}")
    if ply_completos:
        print("\nPrimeros objetos encontrados:")
        for p in sorted(ply_completos)[:5]:
            print(f"  {p.relative_to(DESTINO)}")


def main():
    ap = argparse.ArgumentParser(description="Descarga Fantastic Breaks desde Google Drive.")
    ap.add_argument("--solo-zip", action="store_true", help="Solo descarga el ZIP, no descomprime.")
    args = ap.parse_args()

    zip_path = descargar()
    if zip_path is None:
        return

    if not args.solo_zip:
        descomprimir(zip_path)
        resumen()
    else:
        print(f"\nZIP listo en {zip_path}")
        print("Para descomprimir: python Scripts/descargar_fantastic_breaks.py")


if __name__ == "__main__":
    main()
