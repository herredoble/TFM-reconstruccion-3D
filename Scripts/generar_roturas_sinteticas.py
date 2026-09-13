# -*- coding: utf-8 -*-
"""
Genera pares sintéticos (roto, completo) para entrenar el modelo de reparación E3.

QUÉ HACE
  Para cada modelo .ply de ShapeNet/limpias/ y Objaverse/limpias/:
    1. Lee el modelo y conserva solo el componente conectado más grande
    2. Filtra formas geométricamente inválidas (planas, en aguja, multi-pieza)
    3. Normaliza y submuestrea a N_PUNTOS
    4. Simula una rotura: corte por plano con superficie irregular
    5. Guarda el par: <dataset>_<modelo>_completo.npy  /  <dataset>_<modelo>_roto.npy

CAMBIOS vs v1
  - Carga solo el componente conectado más grande (evita .ply con piezas sueltas)
  - Filtro geométrico (PCA): descarta formas planas, en aguja o casi 2D
  - fraccion_max reducida a 0.50 (antes 0.75) → roturas más pequeñas y realistas
  - fraccion_min reducida a 0.15 (antes 0.25) → variedad en tamaño de rotura
  - Rugosidad en el corte (jitter Gaussiano sobre la proyección) → superficie irregular

FORMATO DE SALIDA (igual que Fantastic Breaks procesado)
  - Arrays numpy float32, shape (N_PUNTOS, 3)
  - Normalizados: centroide en origen, radio máximo = 1
  - Carpeta destino: Datos/sintetico/roturas/

USO BÁSICO
  python Scripts/generar_roturas_sinteticas.py

USO AVANZADO
  python Scripts/generar_roturas_sinteticas.py --fraccion_min 0.15 --fraccion_max 0.50
  python Scripts/generar_roturas_sinteticas.py --rugosidad 0.08 --umbral_pca 0.015
  python Scripts/generar_roturas_sinteticas.py --dry-run --max_por_dataset 50

OPCIONES
  --datasets          shapenet objaverse (cuáles datasets procesar)
  --n_puntos          Puntos por nube de salida (defecto: 2048)
  --fraccion_min      Mínimo de puntos a eliminar en la rotura (defecto: 0.15)
  --fraccion_max      Máximo de puntos a eliminar en la rotura (defecto: 0.50)
  --rugosidad         Desviación estándar del ruido en la superficie de corte (defecto: 0.05)
  --umbral_pca        Ratio mínimo eigenvalor_min/eigenvalor_max para aceptar la forma (defecto: 0.01)
  --max_por_dataset   Límite de modelos por dataset (0 = todos)
  --semilla           Semilla aleatoria para reproducibilidad (defecto: 42)
  --destino           Carpeta de salida (defecto: Datos/sintetico/roturas/)
  --dry-run           Muestra qué haría sin escribir ningún archivo
"""

import argparse
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# SECCIÓN 1: CONFIGURACIÓN
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATASETS = {
    "shapenet":  BASE_DIR / "Datos" / "shapenet"  / "limpias",
    "objaverse": BASE_DIR / "Datos" / "objaverse" / "limpias",
}

DESTINO_DEFAULT = BASE_DIR / "Datos" / "sintetico" / "roturas_v2"


# ---------------------------------------------------------------------------
# SECCIÓN 2: CARGA — solo el componente conectado más grande
# ---------------------------------------------------------------------------

def cargar_componente_mayor(ruta: Path) -> np.ndarray | None:
    """Lee un .ply y devuelve SOLO los vértices del componente conectado más grande.

    El script anterior concatenaba todos los componentes de una escena, lo que
    producía nubes con piezas sueltas (un asa separada del cuerpo, objetos dobles,
    artefactos flotantes). Aquí nos quedamos con el trozo más grande.
    """
    try:
        import trimesh
    except ImportError:
        print("[ERROR] trimesh no instalado. Ejecuta: pip install trimesh")
        sys.exit(1)

    if not ruta.exists():
        return None
    try:
        geom = trimesh.load(str(ruta), process=False, force="mesh")

        # Caso 1: mesh único → dividir en componentes y quedarse con el mayor
        if hasattr(geom, "split"):
            componentes = geom.split(only_watertight=False)
            if not componentes:
                # trimesh a veces devuelve lista vacía aunque el mesh tenga vértices
                if hasattr(geom, "vertices") and len(geom.vertices) >= 100:
                    return np.asarray(geom.vertices, dtype=np.float32)
                return None
            mayor = max(componentes, key=lambda c: len(c.vertices))
            pts = np.asarray(mayor.vertices, dtype=np.float32)
            return pts if len(pts) >= 100 else None

        # Caso 2: escena con múltiples geometrías → tomar la más grande
        if hasattr(geom, "geometry"):
            candidatos = [
                np.asarray(g.vertices, dtype=np.float32)
                for g in geom.geometry.values()
                if hasattr(g, "vertices") and len(g.vertices) >= 100
            ]
            if not candidatos:
                return None
            return max(candidatos, key=len)

        return None

    except Exception as e:
        print(f"  [WARN] No se pudo leer {ruta.name}: {e}")
        return None


# ---------------------------------------------------------------------------
# SECCIÓN 3: FILTRO GEOMÉTRICO
# Descarta formas que no parecen vasijas 3D (planas, lineales, degeneradas).
# ---------------------------------------------------------------------------

def es_vasija_valida(pts_norm: np.ndarray, umbral_pca: float = 0.005) -> tuple[bool, str]:
    """Comprueba si una nube de puntos normalizada tiene forma de vasija 3D.

    Usa PCA sobre los vértices: una vasija ocupa los tres ejes del espacio de
    forma equilibrada. Un objeto plano (disco, lámina) tiene un eigenvalor ≈ 0;
    un objeto lineal (aguja) tiene dos eigenvalores ≈ 0.

    umbral_pca: ratio mínimo eigenvalor_min/eigenvalor_max para considerar la
                forma como tridimensionalmente válida.
                0.005 descarta formas muy degeneradas sin rechazar vasijas con un eje corto.
    """
    if len(pts_norm) < 100:
        return False, "muy pocos vértices"

    centrado = pts_norm - pts_norm.mean(axis=0)
    cov = np.cov(centrado.T)
    vals = np.linalg.eigvalsh(cov)  # eigenvalores en orden creciente

    if vals[-1] <= 0:
        return False, "varianza nula (mesh vacío o degenerado)"

    ratio_min = vals[0] / vals[-1]
    ratio_mid = vals[1] / vals[-1]

    if ratio_min < umbral_pca:
        return False, f"forma plana o lineal (PCA min/max={ratio_min:.4f} < {umbral_pca})"
    if ratio_mid < umbral_pca * 2:
        return False, f"forma casi lineal (PCA mid/max={ratio_mid:.4f} < {umbral_pca*2:.4f})"

    return True, "ok"


# ---------------------------------------------------------------------------
# SECCIÓN 4: NORMALIZACIÓN Y SUBMUESTREO
# ---------------------------------------------------------------------------

def normalizar_unitaria(pts: np.ndarray) -> np.ndarray:
    """Centra la nube en el origen y la escala para que quepa en la esfera unidad."""
    centroide = pts.mean(axis=0)
    pts = pts - centroide
    radio_max = np.max(np.linalg.norm(pts, axis=1))
    if radio_max > 0:
        pts = pts / radio_max
    return pts.astype(np.float32)


def submuestrear(pts: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Selecciona exactamente n puntos de la nube (con o sin reposición según haga falta)."""
    if len(pts) >= n:
        idx = rng.choice(len(pts), size=n, replace=False)
    else:
        idx = rng.choice(len(pts), size=n, replace=True)
    return pts[idx].astype(np.float32)


# ---------------------------------------------------------------------------
# SECCIÓN 5: SIMULACIÓN DE ROTURA — tres modos + despachador aleatorio
#
#  PLANO  (40 %): un semiplano elimina una sección de la vasija.
#                 Simula rotura grande (taza partida en dos).
#  CHIP   (40 %): se elimina una región esférica alrededor de un punto
#                 de impacto. Simula golpe local: mella, esquirla, desconche.
#  CUÑA   (20 %): dos planos que se intersectan eliminan una cuña triangular.
#                 Simula un trozo de borde que se desprende.
#
# Los tres modos añaden rugosidad (jitter Gaussiano) en la superficie de corte
# para que no sean bordes perfectamente nítidos.
# ---------------------------------------------------------------------------

def _rotura_plano(
    pts: np.ndarray,
    fraccion_min: float,
    fraccion_max: float,
    rng: np.random.Generator,
    rugosidad: float,
) -> np.ndarray:
    """Corte por un semiplano aleatorio con superficie rugosa."""
    direccion = rng.standard_normal(3)
    direccion /= np.linalg.norm(direccion)

    proyecciones = pts @ direccion
    if rugosidad > 0:
        proyecciones = proyecciones + rng.normal(0, rugosidad, len(pts))

    fraccion_eliminar = rng.uniform(fraccion_min, fraccion_max)
    n_mantener = max(1, int((1.0 - fraccion_eliminar) * len(pts)))
    threshold = np.partition(proyecciones, n_mantener - 1)[n_mantener - 1]
    return pts[proyecciones <= threshold]


def _rotura_chip(
    pts: np.ndarray,
    fraccion_min: float,
    fraccion_max: float,
    rng: np.random.Generator,
    rugosidad: float,
) -> np.ndarray:
    """Elimina una región esférica alrededor de un punto de impacto aleatorio.

    El radio de la esfera se ajusta para eliminar la fracción pedida de puntos.
    """
    # Elegir punto de impacto: un punto real de la nube (más probable en la superficie)
    centro_idx = rng.integers(0, len(pts))
    centro = pts[centro_idx]

    # Distancias de cada punto al centro de impacto
    distancias = np.linalg.norm(pts - centro, axis=1)

    # Añadir rugosidad a las distancias para que el borde del chip sea irregular
    if rugosidad > 0:
        distancias = distancias + rng.normal(0, rugosidad, len(pts))
        distancias = np.maximum(distancias, 0.0)

    # Radio que elimina la fracción pedida
    fraccion_eliminar = rng.uniform(fraccion_min, fraccion_max)
    n_eliminar = max(1, int(fraccion_eliminar * len(pts)))
    # Radio = distancia al punto número n_eliminar más cercano
    radio = np.partition(distancias, n_eliminar - 1)[n_eliminar - 1]

    return pts[distancias > radio]


def _rotura_cuna(
    pts: np.ndarray,
    fraccion_min: float,
    fraccion_max: float,
    rng: np.random.Generator,
    rugosidad: float,
) -> np.ndarray:
    """Elimina la intersección de dos semiplanos (cuña triangular).

    Simula un trozo de borde que se desprende: los dos planos se intersectan
    en una línea aleatoria y se elimina la zona "dentro" de ambos.
    """
    # Dos direcciones independientes
    d1 = rng.standard_normal(3); d1 /= np.linalg.norm(d1)
    d2 = rng.standard_normal(3); d2 /= np.linalg.norm(d2)

    p1 = pts @ d1
    p2 = pts @ d2

    if rugosidad > 0:
        p1 = p1 + rng.normal(0, rugosidad, len(pts))
        p2 = p2 + rng.normal(0, rugosidad, len(pts))

    # La cuña elimina puntos que superen el umbral en AMBAS proyecciones.
    # Ajustamos cada umbral para que la intersección quite fraccion/2 desde cada lado.
    # En la práctica elimina menos que fraccion_max/2 (por solapamiento parcial),
    # así que lo compensamos usando toda la fracción en cada plano individualmente.
    fraccion_eliminar = rng.uniform(fraccion_min, fraccion_max)
    n_mant = max(1, int((1.0 - fraccion_eliminar) * len(pts)))

    th1 = np.partition(p1, n_mant - 1)[n_mant - 1]
    th2 = np.partition(p2, n_mant - 1)[n_mant - 1]

    # Se elimina lo que supera el umbral en AMBOS planos simultáneamente
    eliminar = (p1 > th1) & (p2 > th2)
    sobrevive = ~eliminar

    # Fallback: si la cuña elimina demasiado o demasiado poco, caemos al plano
    ratio = eliminar.mean()
    if ratio < fraccion_min * 0.5 or ratio > fraccion_max * 1.5:
        return _rotura_plano(pts, fraccion_min, fraccion_max, rng, rugosidad)

    return pts[sobrevive]


# Pesos por modo. Ajustables por CLI (--pesos_modo).
_MODOS = ["plano", "chip", "cuna"]
_PESOS_DEFAULT = [0.40, 0.40, 0.20]


def simular_rotura(
    pts: np.ndarray,
    fraccion_min: float,
    fraccion_max: float,
    rng: np.random.Generator,
    rugosidad: float = 0.05,
    pesos: list[float] | None = None,
) -> tuple[np.ndarray, str]:
    """Elige aleatoriamente un modo de rotura y lo aplica.

    Devuelve (pts_rotos, nombre_modo) para que el log indique qué se usó.
    """
    if pesos is None:
        pesos = _PESOS_DEFAULT

    modo = rng.choice(_MODOS, p=pesos)

    if modo == "plano":
        resultado = _rotura_plano(pts, fraccion_min, fraccion_max, rng, rugosidad)
    elif modo == "chip":
        resultado = _rotura_chip(pts, fraccion_min, fraccion_max, rng, rugosidad)
    else:
        resultado = _rotura_cuna(pts, fraccion_min, fraccion_max, rng, rugosidad)

    return resultado, modo


# ---------------------------------------------------------------------------
# SECCIÓN 6: PROCESADO DE UN DATASET
# ---------------------------------------------------------------------------

def procesar_dataset(
    nombre: str,
    carpeta: Path,
    destino: Path,
    n_puntos: int,
    fraccion_min: float,
    fraccion_max: float,
    rugosidad: float,
    umbral_pca: float,
    pesos: list[float],
    max_modelos: int,
    rng: np.random.Generator,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Procesa todos los .ply de carpeta y guarda pares en destino.

    Devuelve (n_pares_ok, n_filtrados_geometria, n_errores).
    """
    modelos = sorted(carpeta.rglob("*.ply"))
    if max_modelos > 0:
        modelos = modelos[:max_modelos]

    print(f"\n--- Dataset: {nombre} ({len(modelos)} modelos en {carpeta}) ---")

    ok = 0
    filtrados = 0
    errores = 0
    conteo_modos: dict[str, int] = {"plano": 0, "chip": 0, "cuna": 0}

    for ruta in modelos:

        # 1. Cargar solo el componente más grande
        pts_raw = cargar_componente_mayor(ruta)
        if pts_raw is None or len(pts_raw) < 100:
            print(f"  [SKIP] {ruta.stem} — sin puntos o ilegible")
            errores += 1
            continue

        # 2. Normalizar ANTES del filtro geométrico
        pts_norm = normalizar_unitaria(pts_raw)

        # 3. Filtro geométrico: descartar formas que no son vasijas 3D
        valido, motivo = es_vasija_valida(pts_norm, umbral_pca)
        if not valido:
            print(f"  [FILT] {ruta.stem[:45]:<45}  {motivo}")
            filtrados += 1
            continue

        # 4. Ground truth (completo): submuestrear a n_puntos
        pts_completo = submuestrear(pts_norm, n_puntos, rng)

        # 5. Simular la rotura (modo aleatorio)
        pts_roto_raw, modo = simular_rotura(
            pts_norm, fraccion_min, fraccion_max, rng, rugosidad, pesos
        )
        if len(pts_roto_raw) < 10:
            print(f"  [SKIP] {ruta.stem} — rotura dejó muy pocos puntos ({len(pts_roto_raw)})")
            errores += 1
            continue

        conteo_modos[modo] += 1

        # 6. Submuestrear el trozo roto a n_puntos
        pts_roto = submuestrear(pts_roto_raw, n_puntos, rng)

        # 7. Guardar par
        prefijo       = f"{nombre}_{ruta.stem}"
        ruta_completo = destino / f"{prefijo}_completo.npy"
        ruta_roto     = destino / f"{prefijo}_roto.npy"

        # Checkpoint: saltar si el par ya existe (permite relanzar sin repetir trabajo)
        if not dry_run and ruta_completo.exists() and ruta_roto.exists():
            ok += 1
            continue

        estado = "[DRY]" if dry_run else "[OK] "
        pct = 100 * (1 - len(pts_roto_raw) / len(pts_norm))
        print(f"  {estado} [{modo:<5}] {ruta.stem[:37]:<37}  raw:{len(pts_raw):>7,}  "
              f"roto:{len(pts_roto_raw):>5,} pts ({pct:.0f}% eliminado)")

        if not dry_run:
            np.save(ruta_completo, pts_completo)
            np.save(ruta_roto,     pts_roto)

        ok += 1

    if ok > 0:
        print(f"  Modos usados — plano:{conteo_modos['plano']}  "
              f"chip:{conteo_modos['chip']}  cuña:{conteo_modos['cuna']}")

    return ok, filtrados, errores


# ---------------------------------------------------------------------------
# SECCIÓN 7: CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Genera pares sintéticos (roto, completo) para entrenar E3.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python Scripts/generar_roturas_sinteticas.py
  python Scripts/generar_roturas_sinteticas.py --datasets shapenet --max_por_dataset 200
  python Scripts/generar_roturas_sinteticas.py --fraccion_min 0.15 --fraccion_max 0.50
  python Scripts/generar_roturas_sinteticas.py --rugosidad 0.08 --umbral_pca 0.015
  python Scripts/generar_roturas_sinteticas.py --dry-run
        """,
    )
    ap.add_argument(
        "--datasets", nargs="+", default=["shapenet", "objaverse"],
        choices=list(DATASETS.keys()),
    )
    ap.add_argument("--n_puntos",   type=int,   default=2048)
    ap.add_argument("--fraccion_min", type=float, default=0.15,
        help="Mínimo de puntos a eliminar en la rotura (defecto: 0.15)")
    ap.add_argument("--fraccion_max", type=float, default=0.50,
        help="Máximo de puntos a eliminar en la rotura (defecto: 0.50)")
    ap.add_argument("--rugosidad",  type=float, default=0.05,
        help="Desviación estándar del ruido en la superficie de corte (defecto: 0.05)")
    ap.add_argument("--umbral_pca", type=float, default=0.005,
        help="Ratio PCA mínimo para aceptar una forma como vasija (defecto: 0.005)")
    ap.add_argument(
        "--pesos_modo", nargs=3, type=float, default=_PESOS_DEFAULT,
        metavar=("PLANO", "CHIP", "CUNA"),
        help="Probabilidades de cada modo de rotura, deben sumar 1 "
             "(defecto: 0.40 0.40 0.20)",
    )
    ap.add_argument("--max_por_dataset", type=int, default=0)
    ap.add_argument("--semilla",    type=int,   default=42)
    ap.add_argument("--destino",    default=str(DESTINO_DEFAULT))
    ap.add_argument("--dry-run",    action="store_true")

    args    = ap.parse_args()
    pesos   = args.pesos_modo
    if abs(sum(pesos) - 1.0) > 1e-6:
        ap.error(f"--pesos_modo debe sumar 1.0 (suma actual: {sum(pesos):.3f})")

    rng     = np.random.default_rng(args.semilla)
    destino = Path(args.destino)

    if not args.dry_run:
        destino.mkdir(parents=True, exist_ok=True)

    print("\n=== Generación de roturas sintéticas (v2) ===")
    print(f"  Datasets        : {args.datasets}")
    print(f"  Puntos/nube     : {args.n_puntos}")
    print(f"  Fracción rotura : {args.fraccion_min:.0%} – {args.fraccion_max:.0%} eliminado")
    print(f"  Rugosidad corte : {args.rugosidad}")
    print(f"  Modos (p)       : plano={pesos[0]:.2f}  chip={pesos[1]:.2f}  cuña={pesos[2]:.2f}")
    print(f"  Umbral PCA      : {args.umbral_pca}")
    print(f"  Max por dataset : {'todos' if args.max_por_dataset == 0 else args.max_por_dataset}")
    print(f"  Semilla         : {args.semilla}")
    print(f"  Destino         : {destino}")
    print(f"  Dry-run         : {args.dry_run}")

    total_ok  = 0
    total_fil = 0
    total_err = 0

    for nombre in args.datasets:
        carpeta = DATASETS[nombre]
        if not carpeta.exists():
            print(f"\n[SKIP] Dataset '{nombre}': carpeta no encontrada → {carpeta}")
            continue
        ok, fil, err = procesar_dataset(
            nombre=nombre,
            carpeta=carpeta,
            destino=destino,
            n_puntos=args.n_puntos,
            fraccion_min=args.fraccion_min,
            fraccion_max=args.fraccion_max,
            rugosidad=args.rugosidad,
            umbral_pca=args.umbral_pca,
            pesos=pesos,
            max_modelos=args.max_por_dataset,
            rng=rng,
            dry_run=args.dry_run,
        )
        total_ok  += ok
        total_fil += fil
        total_err += err

    print(f"\n=== RESUMEN FINAL ===")
    print(f"  Pares generados  : {total_ok}")
    print(f"  Filtrados (PCA)  : {total_fil}  ← formas no válidas descartadas")
    print(f"  Errores / skips  : {total_err}")

    if not args.dry_run and total_ok > 0:
        archivos = list(destino.glob("*.npy"))
        tam_mb   = sum(f.stat().st_size for f in archivos) / 1e6
        print(f"  Archivos .npy    : {len(archivos)}")
        print(f"  Tamaño total     : {tam_mb:.1f} MB")
        print(f"  Directorio       : {destino}")


if __name__ == "__main__":
    main()
