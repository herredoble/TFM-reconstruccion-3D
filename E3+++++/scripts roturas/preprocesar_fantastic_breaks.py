# -*- coding: utf-8 -*-
"""
Preprocesa Fantastic Breaks para entrenar el modelo de reparación (E3).

Qué hace:
  1. Recorre Datos/fantastic_breaks/<clase>/<objeto>/
  2. Filtra por clases seleccionadas (por defecto: vasijas)
  3. Lee model_c.ply (completo) y model_b_0.ply (roto) de cada objeto
  4. Submuestrea ambos a N_PUNTOS (defecto: 2048)
  5. Guarda pares (roto_2048.npy, completo_2048.npy) en Datos/fantastic_breaks/procesado/

Clases del dataset (Fantastic Breaks, Lamb et al. CVPR 2023):
  00 = mug     (30 pares)   <- vasija
  01 = plate   (35 pares)   <- plato, opcional
  02 = bowl    (17 pares)   <- vasija
  03 = jar     ( 6 pares)   <- vasija  [OJO: en docs anteriores estaba como cup]
  05 = cup     ( 8 pares)   <- vasija  [OJO: en docs anteriores estaba como jar]
  06 = misc    ( 2 pares)
  07 = box/misc( 3 pares)
  09 = statue  (30 pares)   <- opcional (volumen extra)
  10 = misc    ( 1 par)
  12 = coaster ( 6 pares)
  13 = misc    ( 1 par)
  14 = misc    ( 3 pares)
  17 = misc    ( 1 par)
  18 = misc    ( 4 pares)
  19 = box/misc( 3 pares)

Uso básico (solo vasijas, 61 pares):
  python Scripts/preprocesar_fantastic_breaks.py

Uso ampliado (vasijas + plate + statue, 126 pares):
  python Scripts/preprocesar_fantastic_breaks.py --clases vasijas plate statue

Uso con todas las clases (150 pares):
  python Scripts/preprocesar_fantastic_breaks.py --clases todas

Opciones:
  --clases vasijas|plate|statue|todas|00,01,...   Clases a incluir
  --n_puntos 2048                                  Puntos tras submuestreo
  --semilla 42                                     Semilla aleatoria
  --destino Datos/fantastic_breaks/procesado       Carpeta de salida
  --dry-run                                        Muestra qué haría sin escribir
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

BASE_DIR = Path(r"C:\edf\tfm")
DATOS_DIR = BASE_DIR / "Datos" / "fantastic_breaks"

CLASES_INFO = {
    "00": ("mug",     "vasija"),
    "01": ("plate",   "plato"),
    "02": ("bowl",    "vasija"),
    "03": ("jar",     "vasija"),
    "05": ("cup",     "vasija"),
    "06": ("misc",    "misc"),
    "07": ("box",     "misc"),
    "09": ("statue",  "estatua"),
    "10": ("misc",    "misc"),
    "12": ("coaster", "misc"),
    "13": ("misc",    "misc"),
    "14": ("misc",    "misc"),
    "17": ("misc",    "misc"),
    "18": ("misc",    "misc"),
    "19": ("box",     "misc"),
}

GRUPOS = {
    "vasijas": {"00", "02", "03", "05"},
    "plate":   {"01"},
    "statue":  {"09"},
    "todas":   set(CLASES_INFO.keys()),
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def leer_ply_como_array(ruta: Path, _=None) -> np.ndarray | None:
    """Lee un .ply y devuelve array (N, 3) con las coordenadas XYZ.
    Usa trimesh: lee mallas y extrae vértices, o nube de puntos directa."""
    try:
        import trimesh
    except ImportError:
        print("[ERROR] trimesh no está instalado. Ejecuta: pip install trimesh")
        sys.exit(1)

    if not ruta.exists():
        return None
    try:
        geom = trimesh.load(str(ruta), process=False, force="mesh")
        if hasattr(geom, "vertices") and len(geom.vertices) > 0:
            return np.asarray(geom.vertices, dtype=np.float32)
        # Si es una escena con múltiples geometrías
        if hasattr(geom, "geometry"):
            pts_list = [np.asarray(g.vertices, dtype=np.float32)
                        for g in geom.geometry.values()
                        if hasattr(g, "vertices") and len(g.vertices) > 0]
            if pts_list:
                return np.concatenate(pts_list, axis=0)
        return None
    except Exception as e:
        print(f"  [WARN] No se pudo leer {ruta.name}: {e}")
        return None


def submuestrear(pts: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Submuestreo aleatorio a n puntos. Si hay menos puntos, repite."""
    if len(pts) >= n:
        idx = rng.choice(len(pts), size=n, replace=False)
    else:
        idx = rng.choice(len(pts), size=n, replace=True)
    return pts[idx].astype(np.float32)


def normalizar_unitaria(pts: np.ndarray) -> np.ndarray:
    """Centra en el origen y escala a la esfera unidad (radio 1)."""
    centroide = pts.mean(axis=0)
    pts = pts - centroide
    escala = np.max(np.linalg.norm(pts, axis=1))
    if escala > 0:
        pts = pts / escala
    return pts


# ---------------------------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------------------------

def resolver_clases(arg_clases: str) -> set[str]:
    partes = [p.strip() for p in arg_clases.split(",")]
    seleccion = set()
    for parte in partes:
        if parte in GRUPOS:
            seleccion |= GRUPOS[parte]
        elif parte in CLASES_INFO:
            seleccion.add(parte)
        else:
            print(f"[AVISO] Clase o grupo desconocido: '{parte}' — ignorado")
    return seleccion


def procesar(clases_activas: set[str], n_puntos: int, semilla: int,
             destino: Path, dry_run: bool):

    rng = np.random.default_rng(semilla)

    destino.mkdir(parents=True, exist_ok=True)

    # Encabezado informativo
    print("\n=== Preprocesado Fantastic Breaks ===")
    print(f"  Clases activas : {sorted(clases_activas)}")
    print(f"  Puntos por nube: {n_puntos}")
    print(f"  Semilla        : {semilla}")
    print(f"  Destino        : {destino}")
    print(f"  Modo dry-run   : {dry_run}")
    print()

    ok = 0
    errores = []
    omitidos = []

    for clase_dir in sorted(CLASES_INFO.keys()):
        clase_path = DATOS_DIR / clase_dir
        if not clase_path.is_dir():
            continue

        nombre_clase, _ = CLASES_INFO[clase_dir]

        if clase_dir not in clases_activas:
            n_obj = sum(1 for d in clase_path.iterdir() if d.is_dir())
            omitidos.append(f"  {clase_dir} ({nombre_clase}): {n_obj} objetos omitidos")
            continue

        objetos = sorted(d for d in clase_path.iterdir() if d.is_dir())
        print(f"Clase {clase_dir} — {nombre_clase} ({len(objetos)} objetos):")

        for obj_dir in objetos:
            ruta_completo = obj_dir / "model_c.ply"
            ruta_roto     = obj_dir / "model_b_0.ply"

            # Verificar existencia
            if not ruta_completo.exists():
                errores.append(f"  {clase_dir}/{obj_dir.name}: falta model_c.ply")
                print(f"  [SKIP] {obj_dir.name} — falta model_c.ply")
                continue
            if not ruta_roto.exists():
                errores.append(f"  {clase_dir}/{obj_dir.name}: falta model_b_0.ply")
                print(f"  [SKIP] {obj_dir.name} — falta model_b_0.ply")
                continue

            # Leer puntos
            pts_completo = leer_ply_como_array(ruta_completo)
            pts_roto     = leer_ply_como_array(ruta_roto)

            if pts_completo is None or len(pts_completo) == 0:
                errores.append(f"  {clase_dir}/{obj_dir.name}: model_c.ply vacío o ilegible")
                print(f"  [SKIP] {obj_dir.name} — model_c.ply vacío")
                continue
            if pts_roto is None or len(pts_roto) == 0:
                errores.append(f"  {clase_dir}/{obj_dir.name}: model_b_0.ply vacío o ilegible")
                print(f"  [SKIP] {obj_dir.name} — model_b_0.ply vacío")
                continue

            # Submuestrear y normalizar
            sub_completo = normalizar_unitaria(submuestrear(pts_completo, n_puntos, rng))
            sub_roto     = normalizar_unitaria(submuestrear(pts_roto,     n_puntos, rng))

            # Nombre de salida: <clase>_<objeto>_completo/roto.npy
            prefijo = f"{clase_dir}_{obj_dir.name}"
            ruta_out_completo = destino / f"{prefijo}_completo.npy"
            ruta_out_roto     = destino / f"{prefijo}_roto.npy"

            estado = "[DRY-RUN]" if dry_run else "[OK]"
            print(f"  {estado} {obj_dir.name}: "
                  f"completo {len(pts_completo):>8,} -> {n_puntos} pts | "
                  f"roto {len(pts_roto):>8,} -> {n_puntos} pts")

            if not dry_run:
                np.save(ruta_out_completo, sub_completo)
                np.save(ruta_out_roto,     sub_roto)

            ok += 1

    # Resumen final
    print()
    print("=== RESUMEN ===")
    print(f"  Pares procesados : {ok}")
    print(f"  Errores          : {len(errores)}")
    if errores:
        for e in errores:
            print(e)
    if omitidos:
        print(f"\n  Clases omitidas por filtro:")
        for o_ in omitidos:
            print(o_)
    if not dry_run and ok > 0:
        archivos_npy = list(destino.glob("*.npy"))
        tam_mb = sum(f.stat().st_size for f in archivos_npy) / 1e6
        print(f"\n  Archivos .npy generados: {len(archivos_npy)}")
        print(f"  Tamaño total           : {tam_mb:.1f} MB")
        print(f"  Directorio             : {destino}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Preprocesa Fantastic Breaks para entrenamiento E3.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python Scripts/preprocesar_fantastic_breaks.py
  python Scripts/preprocesar_fantastic_breaks.py --clases vasijas,plate
  python Scripts/preprocesar_fantastic_breaks.py --clases todas --n_puntos 8192
  python Scripts/preprocesar_fantastic_breaks.py --dry-run
        """,
    )
    ap.add_argument(
        "--clases", default="vasijas",
        help="Clases a incluir: vasijas | plate | statue | todas | lista 00,01,... (defecto: vasijas)",
    )
    ap.add_argument(
        "--n_puntos", type=int, default=2048,
        help="Número de puntos tras submuestreo (defecto: 2048)",
    )
    ap.add_argument(
        "--semilla", type=int, default=42,
        help="Semilla aleatoria para reproducibilidad (defecto: 42)",
    )
    ap.add_argument(
        "--destino", default=str(DATOS_DIR / "procesado"),
        help="Directorio de salida para los .npy",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Muestra qué haría sin escribir ningún archivo",
    )

    args = ap.parse_args()
    clases_activas = resolver_clases(args.clases)

    if not clases_activas:
        print("[ERROR] Ninguna clase válida seleccionada.")
        sys.exit(1)

    procesar(
        clases_activas=clases_activas,
        n_puntos=args.n_puntos,
        semilla=args.semilla,
        destino=Path(args.destino),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
