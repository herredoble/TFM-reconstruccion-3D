# -*- coding: utf-8 -*-
"""
Genera pares sintéticos (roto, completo) para entrenar el modelo de reparación E3.

QUÉ HACE
  Para cada modelo .ply de ShapeNet/limpias/ y Objaverse/limpias/:
    1. Lee el modelo completo
    2. Lo normaliza (centrado en origen, escala esfera unidad) y submuestrea a N_PUNTOS
    3. Simula una rotura: corta con un plano aleatorio, eliminando entre 25% y 75% de puntos
    4. Submuestrea el trozo roto a N_PUNTOS
    5. Guarda el par: <dataset>_<modelo>_completo.npy  /  <dataset>_<modelo>_roto.npy

POR QUÉ FUNCIONA
  Los modelos de shape completion (PCN, PoinTr, SnowFlakeNet) aprenden a reconstruir
  una nube completa a partir de una parcial. Para entrenar bien necesitan miles de pares
  (roto → completo). Fantastic Breaks aporta 61 pares reales; este script genera ~2.000+
  pares sintéticos. El corte por plano es la técnica estándar en los papers del campo.

FORMATO DE SALIDA (igual que Fantastic Breaks procesado)
  - Arrays numpy float32, shape (N_PUNTOS, 3)
  - Normalizados: centroide en origen, radio máximo = 1
  - Carpeta destino: Datos/sintetico/roturas/

USO BÁSICO
  python Scripts/generar_roturas_sinteticas.py

USO AVANZADO
  python Scripts/generar_roturas_sinteticas.py --datasets shapenet --max_por_dataset 200
  python Scripts/generar_roturas_sinteticas.py --fraccion_min 0.4 --fraccion_max 0.6
  python Scripts/generar_roturas_sinteticas.py --dry-run

OPCIONES
  --datasets        shapenet objaverse (cuáles datasets procesar)
  --n_puntos        Puntos por nube de salida (defecto: 2048)
  --fraccion_min    Mínimo de puntos a eliminar en la rotura (defecto: 0.25)
  --fraccion_max    Máximo de puntos a eliminar en la rotura (defecto: 0.75)
  --max_por_dataset Límite de modelos por dataset (0 = todos)
  --semilla         Semilla aleatoria para reproducibilidad (defecto: 42)
  --destino         Carpeta de salida (defecto: Datos/sintetico/roturas/)
  --dry-run         Muestra qué haría sin escribir ningún archivo
"""

import argparse
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# SECCIÓN 1: CONFIGURACIÓN
# Rutas a los datasets ya procesados y carpeta de salida.
# ---------------------------------------------------------------------------

BASE_DIR = Path(r"C:\edf\tfm")

# Carpetas de entrada: los .ply ya limpios y normalizados de cada dataset
DATASETS = {
    "shapenet":  BASE_DIR / "Datos" / "shapenet"  / "limpias",
    "objaverse": BASE_DIR / "Datos" / "objaverse" / "limpias",
}

# Carpeta de salida: separada de Fantastic Breaks para no mezclar real con sintético
DESTINO_DEFAULT = BASE_DIR / "Datos" / "sintetico" / "roturas"


# ---------------------------------------------------------------------------
# SECCIÓN 2: FUNCIONES DE UTILIDAD
# Las mismas tres funciones que ya están en preprocesar_fantastic_breaks.py.
# Las repetimos aquí para que el script sea autónomo (no depende de otro módulo).
# ---------------------------------------------------------------------------

def leer_ply_como_array(ruta: Path) -> np.ndarray | None:
    """Lee un .ply y devuelve array (N, 3) con las coordenadas XYZ de los vértices."""
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
        # Algunos .ply son escenas con múltiples geometrías — unificamos vértices
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


def normalizar_unitaria(pts: np.ndarray) -> np.ndarray:
    """Centra la nube en el origen y la escala para que quepa en la esfera unidad.

    Convención del proyecto: centroide en (0,0,0), punto más lejano a distancia 1.
    Es la misma normalización que usan PoinTr, PCN y todos los modelos de E3.
    """
    centroide = pts.mean(axis=0)            # punto medio de todos los vértices
    pts = pts - centroide                   # mover el centroide al origen
    radio_max = np.max(np.linalg.norm(pts, axis=1))  # distancia del punto más lejano
    if radio_max > 0:
        pts = pts / radio_max               # escalar para que ese punto quede a distancia 1
    return pts.astype(np.float32)


def submuestrear(pts: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Selecciona aleatoriamente n puntos de la nube.

    Si hay más de n puntos: muestreo sin reposición (cada punto se elige una sola vez).
    Si hay menos de n puntos: muestreo con reposición (algunos puntos se repiten).
    Esto siempre devuelve exactamente n puntos, pase lo que pase.
    """
    if len(pts) >= n:
        idx = rng.choice(len(pts), size=n, replace=False)
    else:
        idx = rng.choice(len(pts), size=n, replace=True)
    return pts[idx].astype(np.float32)


# ---------------------------------------------------------------------------
# SECCIÓN 3: SIMULACIÓN DE ROTURA
# Esta es la función nueva y el núcleo del script.
# ---------------------------------------------------------------------------

def simular_rotura(
    pts: np.ndarray,
    fraccion_min: float,
    fraccion_max: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Simula una fractura cortando la nube con un plano aleatorio.

    La técnica (estándar en papers de shape completion):
      1. Elige una dirección aleatoria en el espacio 3D
      2. Proyecta cada punto sobre esa dirección → cada punto obtiene un número
         · Puntos "al frente" de la dirección → número alto → se eliminan (trozo que falta)
         · Puntos "detrás"                    → número bajo → se conservan (trozo que queda)
      3. El umbral de corte se ajusta para eliminar entre fraccion_min y fraccion_max

    Recibe: pts ya normalizados (todos los vértices del modelo)
    Devuelve: subconjunto de pts que "sobrevive" a la rotura (menos de N puntos)
    """

    # --- Paso 1: dirección aleatoria ---
    # rng.standard_normal(3) genera 3 valores de distribución normal → vector [x, y, z]
    # Al dividir por su norma (longitud) lo convertimos en vector unitario (longitud = 1)
    # Esto da una dirección uniformemente distribuida en la esfera: cualquier ángulo es igual de probable
    direccion = rng.standard_normal(3)
    direccion /= np.linalg.norm(direccion)

    # --- Paso 2: proyección de cada punto sobre la dirección ---
    # pts tiene shape (N, 3) — N puntos, cada uno con coordenadas (x, y, z)
    # pts @ direccion  →  producto escalar fila a fila → shape (N,)
    # Resultado: un número por cada punto que indica qué tan "en esa dirección" está
    proyecciones = pts @ direccion

    # --- Paso 3: decidir cuántos puntos conservar ---
    # La fracción a eliminar es aleatoria entre fraccion_min y fraccion_max
    # Así los pares no son siempre "exactamente la mitad" — hay variedad
    fraccion_eliminar = rng.uniform(fraccion_min, fraccion_max)
    n_total = len(pts)
    n_mantener = max(1, int((1.0 - fraccion_eliminar) * n_total))

    # --- Paso 4: umbral de corte ---
    # Queremos el valor de proyección tal que n_mantener puntos lo tengan por debajo.
    # np.partition reorganiza el array para que el elemento [k] sea el que estaría en
    # la posición k si el array estuviese ordenado — más rápido que ordenar todo.
    threshold = np.partition(proyecciones, n_mantener - 1)[n_mantener - 1]

    # --- Paso 5: filtrar ---
    # Conservamos los puntos con proyección <= threshold (los del lado que "sobrevive")
    pts_roto = pts[proyecciones <= threshold]

    return pts_roto


# ---------------------------------------------------------------------------
# SECCIÓN 4: PROCESADO DE UN DATASET
# Recorre todos los .ply de una carpeta y genera los pares.
# ---------------------------------------------------------------------------

def procesar_dataset(
    nombre: str,
    carpeta: Path,
    destino: Path,
    n_puntos: int,
    fraccion_min: float,
    fraccion_max: float,
    max_modelos: int,
    rng: np.random.Generator,
    dry_run: bool,
) -> tuple[int, int]:
    """Procesa todos los .ply de carpeta y guarda pares en destino.

    Flujo por cada modelo:
      .ply  →  normalizar  →  completo (2048 pts, ground truth)
                           →  simular_rotura  →  roto_raw (< 2048 pts)
                                              →  submuestrear  →  roto (2048 pts, entrada)

    Devuelve (n_pares_ok, n_errores).
    """
    modelos = sorted(carpeta.rglob("*.ply"))

    # Si se pide un límite, tomar solo los primeros N modelos
    if max_modelos > 0:
        modelos = modelos[:max_modelos]

    print(f"\n--- Dataset: {nombre} ({len(modelos)} modelos en {carpeta}) ---")

    ok = 0
    errores = 0

    for ruta in modelos:

        # 1. Leer los vértices del .ply
        pts_raw = leer_ply_como_array(ruta)
        if pts_raw is None or len(pts_raw) < 10:
            print(f"  [SKIP] {ruta.stem} — sin puntos o ilegible")
            errores += 1
            continue

        # 2. Normalizar TODOS los vértices (antes del submuestreo)
        #    Trabajamos con todos los puntos para que el corte sea más preciso
        pts_norm = normalizar_unitaria(pts_raw)

        # 3. Ground truth (completo): submuestrear los vértices normalizados a n_puntos
        pts_completo = submuestrear(pts_norm, n_puntos, rng)

        # 4. Simular la rotura sobre la nube normalizada completa
        #    Usamos pts_norm (todos los vértices) para tener más resolución en el corte
        pts_roto_raw = simular_rotura(pts_norm, fraccion_min, fraccion_max, rng)

        if len(pts_roto_raw) < 10:
            # Esto solo pasa si el corte eliminó casi todo (muy improbable con fraccion_max=0.75)
            print(f"  [SKIP] {ruta.stem} — rotura dejó muy pocos puntos ({len(pts_roto_raw)})")
            errores += 1
            continue

        # 5. Submuestrear el trozo roto a n_puntos
        #    Si quedan <2048 puntos tras el corte, submuestrear repite algunos → OK para entrenamiento
        pts_roto = submuestrear(pts_roto_raw, n_puntos, rng)

        # 6. Guardar par
        #    Nombre: <dataset>_<stem_del_ply>_completo.npy  /  _roto.npy
        prefijo       = f"{nombre}_{ruta.stem}"
        ruta_completo = destino / f"{prefijo}_completo.npy"
        ruta_roto     = destino / f"{prefijo}_roto.npy"

        estado = "[DRY]" if dry_run else "[OK] "
        pct_eliminado = 100 * (1 - len(pts_roto_raw) / len(pts_norm))
        print(f"  {estado} {ruta.stem[:40]:<40}  "
              f"raw:{len(pts_raw):>7,}  roto:{len(pts_roto_raw):>5,} pts ({pct_eliminado:.0f}% eliminado)")

        if not dry_run:
            np.save(ruta_completo, pts_completo)
            np.save(ruta_roto,     pts_roto)

        ok += 1

    return ok, errores


# ---------------------------------------------------------------------------
# SECCIÓN 5: INTERFAZ DE LÍNEA DE COMANDOS (CLI)
# Igual que en preprocesar_fantastic_breaks.py: argparse + función main().
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Genera pares sintéticos (roto, completo) para entrenar E3.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python Scripts/generar_roturas_sinteticas.py
  python Scripts/generar_roturas_sinteticas.py --datasets shapenet --max_por_dataset 200
  python Scripts/generar_roturas_sinteticas.py --fraccion_min 0.4 --fraccion_max 0.6
  python Scripts/generar_roturas_sinteticas.py --dry-run
        """,
    )
    ap.add_argument(
        "--datasets", nargs="+", default=["shapenet", "objaverse"],
        choices=list(DATASETS.keys()),
        help="Datasets a procesar (defecto: shapenet objaverse)",
    )
    ap.add_argument(
        "--n_puntos", type=int, default=2048,
        help="Puntos en cada nube de salida (defecto: 2048)",
    )
    ap.add_argument(
        "--fraccion_min", type=float, default=0.25,
        help="Mínimo de la rotura: fracción de puntos a eliminar (defecto: 0.25)",
    )
    ap.add_argument(
        "--fraccion_max", type=float, default=0.75,
        help="Máximo de la rotura: fracción de puntos a eliminar (defecto: 0.75)",
    )
    ap.add_argument(
        "--max_por_dataset", type=int, default=0,
        help="Límite de modelos por dataset (0 = todos, defecto: 0)",
    )
    ap.add_argument(
        "--semilla", type=int, default=42,
        help="Semilla aleatoria (defecto: 42)",
    )
    ap.add_argument(
        "--destino", default=str(DESTINO_DEFAULT),
        help="Carpeta de salida para los .npy",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Muestra qué haría sin escribir ningún archivo",
    )

    args = ap.parse_args()
    rng     = np.random.default_rng(args.semilla)
    destino = Path(args.destino)

    if not args.dry_run:
        destino.mkdir(parents=True, exist_ok=True)

    print("\n=== Generación de roturas sintéticas ===")
    print(f"  Datasets        : {args.datasets}")
    print(f"  Puntos/nube     : {args.n_puntos}")
    print(f"  Fracción rotura : {args.fraccion_min:.0%} – {args.fraccion_max:.0%} de puntos eliminados")
    print(f"  Max por dataset : {'todos' if args.max_por_dataset == 0 else args.max_por_dataset}")
    print(f"  Semilla         : {args.semilla}")
    print(f"  Destino         : {destino}")
    print(f"  Dry-run         : {args.dry_run}")

    total_ok  = 0
    total_err = 0

    for nombre in args.datasets:
        carpeta = DATASETS[nombre]
        if not carpeta.exists():
            print(f"\n[SKIP] Dataset '{nombre}': carpeta no encontrada → {carpeta}")
            continue
        ok, err = procesar_dataset(
            nombre=nombre,
            carpeta=carpeta,
            destino=destino,
            n_puntos=args.n_puntos,
            fraccion_min=args.fraccion_min,
            fraccion_max=args.fraccion_max,
            max_modelos=args.max_por_dataset,
            rng=rng,
            dry_run=args.dry_run,
        )
        total_ok  += ok
        total_err += err

    print(f"\n=== RESUMEN FINAL ===")
    print(f"  Pares generados : {total_ok}")
    print(f"  Errores / skips : {total_err}")

    if not args.dry_run and total_ok > 0:
        archivos = list(destino.glob("*.npy"))
        tam_mb   = sum(f.stat().st_size for f in archivos) / 1e6
        print(f"  Archivos .npy   : {len(archivos)}")
        print(f"  Tamaño total    : {tam_mb:.1f} MB")
        print(f"  Directorio      : {destino}")
        print(f"\n  Listo. Rocío puede usar estos datos para entrenar E3.")


if __name__ == "__main__":
    main()
