"""
Descarga el dataset CO3D (Common Objects in 3D, Meta Research)
para las categorías de vasijas/recipientes usadas en el TFM.

CO3D v2 — GitHub: https://github.com/facebookresearch/co3d
Licencia: CC BY-NC 4.0

Categorías descargadas:
  cup      (~450 secuencias, ~3 GB)  — fotos reales de tazas/vasos
  bowl     (~420 secuencias, ~3 GB)  — cuencos
  vase     (~360 secuencias, ~2 GB)  — jarrones

Uso:
  python descargar_co3d.py              # descarga cup + bowl + vase
  python descargar_co3d.py --solo cup   # solo una categoría
"""

import subprocess
import sys
import shutil
import argparse
from pathlib import Path

DESTINO = Path(r"C:\EDF\TFM\Datos\co3d\raw")
REPO_DIR = Path(r"C:\EDF\TFM\Datos\co3d\repo")

# Categorías de vasijas/recipientes disponibles en CO3D
CATEGORIAS_VASIJAS = ["cup", "bowl", "vase"]

# Categorías extra opcionales (comentadas; activar en P1 si se quiere ampliar)
# CATEGORIAS_EXTRA = ["wineglass", "bottle"]


def clonar_co3d():
    if REPO_DIR.exists():
        print(f"[OK] Repositorio CO3D ya existe en {REPO_DIR}")
        return
    print("Clonando repositorio CO3D (solo la carpeta de descarga, sin historial)...")
    subprocess.run(
        ["git", "clone", "--depth", "1",
         "https://github.com/facebookresearch/co3d.git",
         str(REPO_DIR)],
        check=True
    )
    print("[OK] Repositorio clonado.")


def instalar_dependencias():
    print("Instalando dependencias de CO3D...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-e", str(REPO_DIR)],
        check=True
    )
    print("[OK] Dependencias instaladas.")


def descargar_categorias(categorias: list):
    script = REPO_DIR / "co3d" / "download_dataset.py"
    if not script.exists():
        script = REPO_DIR / "download_dataset.py"

    print(f"\n{'='*55}")
    print(f"  Descargando: {', '.join(categorias)}")
    print(f"  Destino:     {DESTINO}")
    print(f"{'='*55}")

    DESTINO.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [sys.executable, str(script),
         "--download_folder", str(DESTINO),
         "--download_categories", ",".join(categorias)],
        check=True
    )


def resumen():
    print("\n" + "="*55)
    print("  RESUMEN DE DESCARGA CO3D")
    print("="*55)
    total_seq = 0
    for categoria in CATEGORIAS_VASIJAS:
        cat_dir = DESTINO / categoria
        if not cat_dir.exists():
            print(f"  {categoria:<10} — no descargada")
            continue
        secuencias = [d for d in cat_dir.iterdir() if d.is_dir()]
        total_seq += len(secuencias)
        # Tamaño aproximado
        tamano_mb = sum(
            f.stat().st_size for f in cat_dir.rglob("*") if f.is_file()
        ) / 1_048_576
        print(f"  {categoria:<10} — {len(secuencias):>4} secuencias  ({tamano_mb:>7.0f} MB)")
    print(f"  {'TOTAL':<10} — {total_seq:>4} secuencias")
    print(f"\n  Datos en: {DESTINO}")
    print("\nSiguiente paso: usar estas secuencias para:")
    print("  - Etapa 1: validar pipeline de captura con fotos reales")
    print("  - Etapa 2: entrenar/validar reconstrucción 3D (P0/P1)")


def main():
    parser = argparse.ArgumentParser(description="Descarga CO3D para el TFM")
    parser.add_argument(
        "--solo", metavar="CATEGORIA",
        help="Descargar solo esta categoría (cup, bowl o vase)"
    )
    args = parser.parse_args()

    clonar_co3d()
    instalar_dependencias()

    categorias = [args.solo] if args.solo else CATEGORIAS_VASIJAS

    for cat in categorias:
        if cat not in CATEGORIAS_VASIJAS:
            print(f"[AVISO] '{cat}' no está en la lista de vasijas. Categorías válidas: {CATEGORIAS_VASIJAS}")
            return

    descargar_categorias(categorias)
    resumen()


if __name__ == "__main__":
    main()
