"""
AUDITORÍA DRIVE → GITHUB — TFM Reconstrucción 3D
=================================================
Ejecutar en Google Colab (una sola celda basta).

Objetivo: listar TODOS los ficheros relevantes del Drive del TFM con suficiente
información para que podamos decidir qué hay que descargar y subir a GitHub.

Salida:
  - Por pantalla: listado estructurado por carpeta
  - En Drive:     informe_auditoria_drive.txt  (pégalo en el chat con Claude)

Ajusta RUTAS_A_EXPLORAR si tus carpetas tienen nombres distintos.
"""

# ── 0. Montar Drive ───────────────────────────────────────────────────────────
from google.colab import drive
drive.mount("/content/drive", force_remount=False)

import os, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── 1. Configuración — EDITA AQUÍ SI ES NECESARIO ────────────────────────────

# Raíz de tu Drive
MI_UNIDAD = Path("/content/drive/MyDrive")

# Carpetas del TFM que quieres explorar (todas las rutas posibles)
RUTAS_A_EXPLORAR = [
    # Código / notebooks
    "TFM",
    "TFM-reconstruccion-3D",
    "TFM reconstruccion 3D",
    # Datos E2
    "Datos_E2_E3",
    "E2",
    "Pix2Vox",
    # Datos E3
    "E3",
    "Raquel",          # subcarpeta personal dentro de alguna carpeta TFM
    "fantastic_breaks_procesado",
    "shapenet_limpias",
    "objaverse_limpias",
    # Modelos
    "modelos",
    "checkpoints",
    # E4 / E5
    "E4",
    "E5",
]

# Extensiones que nos interesan para GitHub
EXT_CODIGO    = {".py", ".ipynb"}
EXT_MODELO    = {".pt", ".pth", ".ckpt"}
EXT_DATOS     = {".npy", ".ply", ".obj", ".stl", ".csv", ".json"}
EXT_DOC       = {".tex", ".bib", ".md", ".txt"}
EXT_IGNORAR   = {".DS_Store", ".pyc", ".tmp", ".log", ""}

# Palabras clave que indican versión "final" en el nombre del fichero
PALABRAS_FINAL = ["final", "FINAL", "[FINAL]", "v6", "v5_obj", "v5_sn",
                   "mejor", "best", "demo", "pipeline", "app"]
PALABRAS_DESCARTE = ["_EJEC", "_ERROR", "_prueba", "ejecutado",
                      "(2)", "(3)", "_bak", "_old", "_backup"]

# ── 2. Utilidades ─────────────────────────────────────────────────────────────

def fecha(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def tam(b: int) -> str:
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.0f}{u}"
        b //= 1024
    return f"{b:.0f}GB"

def es_final(nombre: str) -> bool:
    return any(p in nombre for p in PALABRAS_FINAL)

def es_descarte(nombre: str) -> bool:
    return any(p in nombre for p in PALABRAS_DESCARTE)

def clasificar(nombre: str) -> str:
    if es_descarte(nombre): return "DESCARTAR"
    if es_final(nombre):    return "FINAL ✅"
    return "revisar"

# ── 3. Escaneo ────────────────────────────────────────────────────────────────

class FileRecord:
    __slots__ = ("ruta","nombre","ext","tamanyo","mtime","carpeta_raiz")
    def __init__(self, path: Path, raiz: Path):
        st = path.stat()
        self.ruta        = path
        self.nombre      = path.name
        self.ext         = path.suffix.lower()
        self.tamanyo     = st.st_size
        self.mtime       = st.st_mtime
        self.carpeta_raiz = raiz.name

def escanear(ruta: Path, raiz: Path, registros: list, profundidad: int = 0):
    if profundidad > 7:
        return
    try:
        for item in sorted(ruta.iterdir()):
            if item.is_symlink():
                continue
            if item.is_dir():
                escanear(item, raiz, registros, profundidad + 1)
            elif item.is_file():
                ext = item.suffix.lower()
                if ext in EXT_IGNORAR:
                    continue
                registros.append(FileRecord(item, raiz))
    except PermissionError:
        pass

def encontrar_y_escanear():
    registros = []
    carpetas_encontradas = []

    for candidato in RUTAS_A_EXPLORAR:
        ruta = MI_UNIDAD / candidato
        if ruta.exists() and ruta.is_dir():
            print(f"  📁 Encontrado: {ruta}")
            carpetas_encontradas.append(ruta)
            escanear(ruta, ruta, registros)

    # Buscar también en raíz de Drive por si hay carpetas no listadas
    try:
        for item in sorted(MI_UNIDAD.iterdir()):
            if item.is_dir() and item not in carpetas_encontradas:
                nombre = item.name.lower()
                if any(k in nombre for k in ["tfm","e2","e3","e4","e5","pix2vox",
                                               "pointr","pcn","shapenet","objaverse",
                                               "fantastic","rotura","reconstruccion"]):
                    print(f"  📁 Encontrado (búsqueda extra): {item}")
                    carpetas_encontradas.append(item)
                    escanear(item, item, registros)
    except PermissionError:
        pass

    return registros

# ── 4. Generación del informe ─────────────────────────────────────────────────

def generar_informe(registros: list[FileRecord]) -> list[str]:
    lineas = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas += [
        "=" * 72,
        "  AUDITORÍA DRIVE → GITHUB  |  TFM Reconstrucción 3D",
        f"  Generado: {ts}   |   Total ficheros escaneados: {len(registros)}",
        "=" * 72,
        "",
    ]

    # ── A. Notebooks (.ipynb) ─────────────────────────────────────────────────
    nbs = [r for r in registros if r.ext == ".ipynb"]
    lineas += [
        "─" * 72,
        f"  A. NOTEBOOKS  ({len(nbs)} ficheros)",
        "  Columnas: ESTADO | FECHA MODIF | TAMAÑO | RUTA RELATIVA",
        "─" * 72,
    ]
    # Agrupar por carpeta raíz
    por_carpeta: dict[str, list] = defaultdict(list)
    for r in nbs:
        por_carpeta[r.carpeta_raiz].append(r)

    for carpeta, items in sorted(por_carpeta.items()):
        lineas.append(f"\n  📁 {carpeta}/")
        for r in sorted(items, key=lambda x: -x.mtime):
            estado = clasificar(r.nombre)
            ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
            lineas.append(
                f"    [{estado:<12}]  {fecha(r.mtime)}  {tam(r.tamanyo):>7}  {ruta_rel}"
            )

    # ── B. Scripts Python (.py) ───────────────────────────────────────────────
    pys = [r for r in registros if r.ext == ".py"]
    lineas += [
        "",
        "─" * 72,
        f"  B. SCRIPTS PYTHON  ({len(pys)} ficheros)",
        "─" * 72,
    ]
    for r in sorted(pys, key=lambda x: -x.mtime):
        ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
        lineas.append(f"    {fecha(r.mtime)}  {tam(r.tamanyo):>7}  {ruta_rel}")

    # ── C. Modelos / checkpoints ──────────────────────────────────────────────
    mods = [r for r in registros if r.ext in EXT_MODELO]
    lineas += [
        "",
        "─" * 72,
        f"  C. MODELOS / CHECKPOINTS  ({len(mods)} ficheros)",
        "─" * 72,
    ]
    for r in sorted(mods, key=lambda x: -x.mtime):
        ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
        lineas.append(f"    {fecha(r.mtime)}  {tam(r.tamanyo):>8}  {r.nombre}")
        lineas.append(f"      → {ruta_rel}")

    # ── D. Ficheros de datos clave ────────────────────────────────────────────
    datos = [r for r in registros if r.ext in EXT_DATOS and r.ext != ".csv"]
    por_ext: dict[str, list] = defaultdict(list)
    for r in datos:
        por_ext[r.ext].append(r)
    lineas += [
        "",
        "─" * 72,
        f"  D. FICHEROS DE DATOS  ({len(datos)} ficheros)",
        "─" * 72,
    ]
    for ext, items in sorted(por_ext.items()):
        total = sum(r.tamanyo for r in items)
        lineas.append(f"  {ext}  ×{len(items)}  total {tam(total)}")
        for r in sorted(items, key=lambda x: -x.mtime)[:10]:
            ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
            lineas.append(f"    {fecha(r.mtime)}  {tam(r.tamanyo):>8}  {ruta_rel}")
        if len(items) > 10:
            lineas.append(f"    ... y {len(items)-10} más")

    # ── E. CSVs / métricas ────────────────────────────────────────────────────
    csvs = [r for r in registros if r.ext == ".csv"]
    lineas += [
        "",
        "─" * 72,
        f"  E. CSVs / MÉTRICAS  ({len(csvs)} ficheros)",
        "─" * 72,
    ]
    for r in sorted(csvs, key=lambda x: -x.mtime):
        ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
        lineas.append(f"    {fecha(r.mtime)}  {tam(r.tamanyo):>7}  {ruta_rel}")

    # ── F. Resumen ejecutivo ──────────────────────────────────────────────────
    nb_finales   = [r for r in nbs if es_final(r.nombre)]
    nb_descartar = [r for r in nbs if es_descarte(r.nombre)]
    nb_revisar   = [r for r in nbs if not es_final(r.nombre) and not es_descarte(r.nombre)]

    lineas += [
        "",
        "=" * 72,
        "  RESUMEN EJECUTIVO",
        "=" * 72,
        f"  Notebooks FINAL ✅  : {len(nb_finales)}",
        f"  Notebooks a REVISAR : {len(nb_revisar)}",
        f"  Notebooks DESCARTAR : {len(nb_descartar)}",
        f"  Scripts Python      : {len(pys)}",
        f"  Checkpoints/modelos : {len(mods)}",
        f"  Ficheros de datos   : {len(datos)}",
        "",
        "  NOTEBOOKS FINAL (candidatos a subir a GitHub):",
    ]
    for r in sorted(nb_finales, key=lambda x: -x.mtime):
        ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
        lineas.append(f"    ✅ {r.nombre}")
        lineas.append(f"       {ruta_rel}")

    lineas += [
        "",
        "  NOTEBOOKS A REVISAR (sin indicador claro de versión final):",
    ]
    for r in sorted(nb_revisar, key=lambda x: -x.mtime):
        ruta_rel = str(r.ruta).replace(str(MI_UNIDAD), "MyDrive")
        lineas.append(f"    ❓ {r.nombre}")
        lineas.append(f"       {ruta_rel}")

    lineas += ["", "=" * 72]
    return lineas


# ── 5. Main ───────────────────────────────────────────────────────────────────

print("Escaneando Drive...")
registros = encontrar_y_escanear()
print(f"Total ficheros encontrados: {len(registros)}\n")

lineas = generar_informe(registros)
informe = "\n".join(lineas)

# Guardar en Drive
ruta_out = MI_UNIDAD / "informe_auditoria_drive.txt"
with open(ruta_out, "w", encoding="utf-8") as f:
    f.write(informe)

# Imprimir por pantalla (Colab lo muestra en el output de la celda)
print(informe)
print(f"\n✅ Informe guardado en: {ruta_out}")
print("\n👉 Copia todo el texto de arriba y pégalo en el chat con Claude.")
