"""
AUDITORÍA DRIVE → GITHUB — TFM Reconstrucción 3D
Versión rápida: salta carpetas de datasets grandes, solo escanea código.
Tiempo estimado: < 2 minutos.
"""

from google.colab import drive
drive.mount("/content/drive", force_remount=False)

import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MI_UNIDAD = Path("/content/drive/MyDrive")

# ── Carpetas de DATOS GRANDES: solo contar, no listar fichero a fichero ───────
CARPETAS_DATOS_PESADOS = {
    "shapenet_limpias", "objaverse_limpias", "fantastic_breaks_procesado",
    "ShapeNet", "shapenet", "Objaverse", "objaverse",
    "roturas", "roturas_centradas", "roturas_v2", "roturas_v3",
    "ModelNet", "modelnet",
    # añade aquí si hay más carpetas con miles de ficheros
}

# ── Carpetas de código/notebooks que SÍ queremos escanear ────────────────────
CARPETAS_CODIGO = [
    "TFM", "TFM-reconstruccion-3D", "TFM reconstruccion 3D",
    "E2", "E3", "E4", "E5",
    "Raquel", "Rocio", "Alvaro", "Almudena", "Luis",
    "Scripts", "scripts",
    "Pix2Vox", "PoinTr", "PCN",
    "modelos", "checkpoints",
    "app", "gradio",
    "Datos_E2_E3",  # entramos pero saltamos subcarpetas de datos
]

EXT_CODIGO  = {".py", ".ipynb"}
EXT_MODELO  = {".pt", ".pth", ".ckpt"}
EXT_METRICA = {".csv", ".json", ".txt"}

PALABRAS_FINAL    = ["final", "FINAL", "[FINAL]", "[ACM]", "v6", "v5_obj",
                     "v5_sn", "mejor", "best", "demo", "pipeline", "app",
                     "NO TOCAR", "_v6_", "_v5_"]
PALABRAS_DESCARTAR = ["_EJEC", "_ERROR", "_prueba", "ejecutado",
                       " (2)", " (3)", "_bak", "_old", "_backup", "_copy"]

def fecha(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def tam(b):
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024: return f"{b:.0f}{u}"
        b //= 1024
    return f"{b:.0f}GB"

def clasif(nombre):
    if any(p in nombre for p in PALABRAS_DESCARTAR): return "DESCARTAR ❌"
    if any(p in nombre for p in PALABRAS_FINAL):     return "FINAL ✅   "
    return "revisar ❓  "

# ── Escaneo rápido ────────────────────────────────────────────────────────────

registros_codigo  = []  # notebooks y .py
registros_modelos = []  # .pt .pth .ckpt
registros_metricas= []  # .csv .json
resumen_datos     = []  # carpetas de datos (solo count)

def escanear(ruta: Path, profundidad: int = 0):
    if profundidad > 6:
        return
    try:
        items = list(ruta.iterdir())
    except PermissionError:
        return

    for item in sorted(items):
        if item.is_symlink():
            continue
        if item.is_dir():
            if item.name in CARPETAS_DATOS_PESADOS:
                # Solo contamos, no entramos
                try:
                    n = sum(1 for _ in item.rglob("*") if _.is_file())
                    resumen_datos.append((item, n))
                    print(f"    [datos pesados, {n} fich] {item.name}/  ← saltado")
                except Exception:
                    resumen_datos.append((item, "?"))
                    print(f"    [datos pesados, ? fich]  {item.name}/  ← saltado")
            else:
                escanear(item, profundidad + 1)
        elif item.is_file():
            ext = item.suffix.lower()
            try:
                st = item.stat()
            except OSError:
                continue
            rec = (item, st.st_size, st.st_mtime)
            if ext in EXT_CODIGO:
                registros_codigo.append(rec)
            elif ext in EXT_MODELO:
                registros_modelos.append(rec)
            elif ext in EXT_METRICA:
                registros_metricas.append(rec)

# Localizar y escanear carpetas de código
carpetas_vistas = set()
for candidato in CARPETAS_CODIGO:
    ruta = MI_UNIDAD / candidato
    if ruta.exists() and ruta.is_dir() and ruta not in carpetas_vistas:
        print(f"  📁 Escaneando: {ruta.name}/")
        carpetas_vistas.add(ruta)
        escanear(ruta)

# Búsqueda extra: carpetas en raíz de Drive con nombres relacionados con el TFM
try:
    for item in sorted(MI_UNIDAD.iterdir()):
        if item.is_dir() and item not in carpetas_vistas:
            n = item.name.lower()
            if any(k in n for k in ["tfm","e2","e3","e4","e5","pix2vox","pointr",
                                     "pcn","rotura","reconstruccion","raquel"]):
                print(f"  📁 Encontrado extra: {item.name}/")
                carpetas_vistas.add(item)
                escanear(item)
except PermissionError:
    pass

print(f"\nEscaneo terminado. Generando informe...\n")

# ── Informe ───────────────────────────────────────────────────────────────────

lineas = []
ts = datetime.now().strftime("%Y-%m-%d %H:%M")
lineas += [
    "=" * 72,
    "  AUDITORÍA DRIVE → GITHUB  |  TFM Reconstrucción 3D",
    f"  {ts}",
    "=" * 72,
    "",
]

# A. Notebooks
nbs = [(p, s, m) for p, s, m in registros_codigo if p.suffix.lower() == ".ipynb"]
lineas += [
    "─" * 72,
    f"  A. NOTEBOOKS  ({len(nbs)} ficheros)",
    "  [ ESTADO       ]  FECHA MODIF    TAMAÑO   RUTA",
    "─" * 72,
]
por_carpeta = defaultdict(list)
for rec in nbs:
    por_carpeta[rec[0].parent].append(rec)

for carpeta in sorted(por_carpeta):
    ruta_rel = str(carpeta).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"\n  📁 {ruta_rel}/")
    for path, size, mtime in sorted(por_carpeta[carpeta], key=lambda x: -x[2]):
        lineas.append(
            f"    [{clasif(path.name)}]  {fecha(mtime)}  {tam(size):>6}   {path.name}"
        )

# B. Scripts Python
pys = [(p, s, m) for p, s, m in registros_codigo if p.suffix.lower() == ".py"]
lineas += [
    "", "─" * 72,
    f"  B. SCRIPTS PYTHON  ({len(pys)} ficheros)",
    "─" * 72,
]
for path, size, mtime in sorted(pys, key=lambda x: -x[2]):
    ruta_rel = str(path).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    {fecha(mtime)}  {tam(size):>6}   {ruta_rel}")

# C. Checkpoints
lineas += [
    "", "─" * 72,
    f"  C. CHECKPOINTS / MODELOS  ({len(registros_modelos)} ficheros)",
    "─" * 72,
]
for path, size, mtime in sorted(registros_modelos, key=lambda x: -x[2]):
    ruta_rel = str(path).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    {fecha(mtime)}  {tam(size):>8}   {path.name}")
    lineas.append(f"      → {ruta_rel}")

# D. Métricas / CSVs
lineas += [
    "", "─" * 72,
    f"  D. MÉTRICAS / CSVs / JSONs  ({len(registros_metricas)} ficheros)",
    "─" * 72,
]
for path, size, mtime in sorted(registros_metricas, key=lambda x: -x[2]):
    ruta_rel = str(path).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    {fecha(mtime)}  {tam(size):>6}   {ruta_rel}")

# E. Datos pesados (resumen)
lineas += [
    "", "─" * 72,
    f"  E. CARPETAS DE DATOS (saltadas, solo conteo)  ({len(resumen_datos)} carpetas)",
    "─" * 72,
]
for ruta, n in resumen_datos:
    ruta_rel = str(ruta).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    {n:>6} ficheros   {ruta_rel}")

# F. Resumen ejecutivo
nb_final    = [(p,s,m) for p,s,m in nbs if "FINAL" in clasif(p.name)]
nb_revisar  = [(p,s,m) for p,s,m in nbs if "revisar" in clasif(p.name)]
nb_descartar= [(p,s,m) for p,s,m in nbs if "DESCARTAR" in clasif(p.name)]

lineas += [
    "", "=" * 72,
    "  F. RESUMEN EJECUTIVO — candidatos a descargar para GitHub",
    "=" * 72,
    f"  Notebooks FINAL ✅   : {len(nb_final)}",
    f"  Notebooks a revisar  : {len(nb_revisar)}",
    f"  Notebooks a descartar: {len(nb_descartar)}",
    f"  Scripts Python       : {len(pys)}",
    f"  Checkpoints          : {len(registros_modelos)}",
    "",
    "  NOTEBOOKS FINAL (descargar y subir a GitHub):",
]
for path, size, mtime in sorted(nb_final, key=lambda x: -x[2]):
    ruta_rel = str(path).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    ✅  {path.name}")
    lineas.append(f"        {ruta_rel}")

lineas += ["", "  NOTEBOOKS A REVISAR (decide tú):"]
for path, size, mtime in sorted(nb_revisar, key=lambda x: -x[2]):
    ruta_rel = str(path).replace(str(MI_UNIDAD), "MyDrive")
    lineas.append(f"    ❓  {path.name}")
    lineas.append(f"        {ruta_rel}")

lineas += ["", "=" * 72,
           "  FIN DEL INFORME — pega todo esto en el chat con Claude",
           "=" * 72]

informe = "\n".join(lineas)

# Guardar
ruta_out = MI_UNIDAD / "informe_auditoria_drive.txt"
with open(ruta_out, "w", encoding="utf-8") as f:
    f.write(informe)

print(informe)
print(f"\n✅ Guardado en: {ruta_out}")
print("👉 Copia todo el texto de arriba y pégalo en el chat con Claude.")
