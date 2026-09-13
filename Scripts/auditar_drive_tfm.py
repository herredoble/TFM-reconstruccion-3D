"""
Auditoría completa del Drive del TFM — ejecutar en Google Colab.

Genera un informe con:
  - Estructura de carpetas TFM en Drive
  - Nº de ficheros, tamaño y tipos por carpeta
  - Checkpoints/modelos disponibles
  - Datasets y estado de los datos

Uso en Colab:
    1. Ejecutar la celda de montaje de Drive (ver abajo)
    2. Cambiar RUTA_BASE si tu carpeta TFM se llama diferente
    3. Ejecutar todo el script

El informe final se guarda en Drive como informe_drive_tfm.txt
"""

# ── Celda 1: montar Drive ─────────────────────────────────────────────────────
from google.colab import drive
drive.mount("/content/drive", force_remount=False)

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuración ─────────────────────────────────────────────────────────────
RUTA_BASE = Path("/content/drive/MyDrive")

# Posibles nombres de la carpeta raíz del TFM (prueba uno a uno)
CANDIDATOS_TFM = [
    "TFM",
    "TFM-reconstruccion-3D",
    "TFM reconstruccion 3D",
    "TFM_3D",
    "Datos_E2_E3",   # carpeta de datos que mencionaba Raquel
]

# Subcarpetas relevantes dentro de TFM/Drive
SUBCARPETAS_ETAPAS = {
    "E2": ["E2", "E2_Pix2Vox", "Pix2Vox", "checkpoints_e2"],
    "E3_datos": ["E3", "fantastic_breaks_procesado", "shapenet_limpias", "objaverse_limpias", "roturas"],
    "E3_modelos": ["modelos", "modelos_e3", "checkpoints", "best.pt"],
    "E4": ["E4", "STL", "mallas_reparadas"],
    "E5": ["E5", "app", "gradio"],
}

EXTENSIONES_DATOS = {".npy", ".ply", ".obj", ".stl", ".glb", ".h5"}
EXTENSIONES_MODELO = {".pt", ".pth", ".ckpt", ".pkl"}
EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
EXTENSIONES_NOTEBOOK = {".ipynb"}
EXTENSIONES_DOC = {".pdf", ".docx", ".tex", ".md", ".txt", ".csv"}


# ── Funciones ─────────────────────────────────────────────────────────────────

def tamanyo_legible(bytes_: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {u}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def analizar_carpeta(ruta: Path, max_depth: int = 4, depth: int = 0) -> dict:
    """Recorre recursivamente una carpeta y devuelve estadísticas."""
    stats = {
        "ruta": str(ruta),
        "depth": depth,
        "subdirs": [],
        "n_ficheros": 0,
        "tamanyo_total": 0,
        "por_extension": defaultdict(int),
        "modelos": [],
        "datasets": [],
        "notebooks": [],
        "ultima_modificacion": None,
    }
    if not ruta.exists() or not ruta.is_dir():
        return stats

    try:
        items = list(ruta.iterdir())
    except PermissionError:
        return stats

    for item in sorted(items):
        if item.is_symlink():
            continue
        if item.is_dir():
            if depth < max_depth:
                sub = analizar_carpeta(item, max_depth, depth + 1)
                stats["subdirs"].append(sub)
                stats["n_ficheros"] += sub["n_ficheros"]
                stats["tamanyo_total"] += sub["tamanyo_total"]
                for ext, cnt in sub["por_extension"].items():
                    stats["por_extension"][ext] += cnt
                stats["modelos"].extend(sub["modelos"])
                stats["datasets"].extend(sub["datasets"])
                stats["notebooks"].extend(sub["notebooks"])
        elif item.is_file():
            try:
                sz = item.stat().st_size
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
            except OSError:
                continue
            ext = item.suffix.lower()
            stats["n_ficheros"] += 1
            stats["tamanyo_total"] += sz
            stats["por_extension"][ext] += 1
            if stats["ultima_modificacion"] is None or mtime > stats["ultima_modificacion"]:
                stats["ultima_modificacion"] = mtime

            if ext in EXTENSIONES_MODELO:
                stats["modelos"].append({
                    "nombre": item.name,
                    "ruta": str(item),
                    "tamanyo": sz,
                    "fecha": mtime.strftime("%Y-%m-%d %H:%M"),
                })
            elif ext in EXTENSIONES_DATOS:
                stats["datasets"].append({
                    "nombre": item.name,
                    "ruta": str(item),
                    "tamanyo": sz,
                })
            elif ext in EXTENSIONES_NOTEBOOK:
                stats["notebooks"].append({
                    "nombre": item.name,
                    "ruta": str(item),
                    "fecha": mtime.strftime("%Y-%m-%d %H:%M"),
                })

    return stats


def imprimir_arbol(stats: dict, indent: int = 0) -> list[str]:
    """Convierte estadísticas en líneas de texto para el informe."""
    lineas = []
    nombre = Path(stats["ruta"]).name
    prefix = "  " * indent
    fecha = stats["ultima_modificacion"].strftime("%Y-%m-%d") if stats["ultima_modificacion"] else "—"
    lineas.append(
        f"{prefix}📁 {nombre}/"
        f"  [{stats['n_ficheros']} fich, {tamanyo_legible(stats['tamanyo_total'])}, último: {fecha}]"
    )
    # tipos de fichero más comunes
    if stats["por_extension"]:
        top = sorted(stats["por_extension"].items(), key=lambda x: -x[1])[:5]
        tipos = "  ".join(f"{ext or '(sin ext)'}×{n}" for ext, n in top)
        lineas.append(f"{prefix}   tipos: {tipos}")
    # subdirs
    for sub in stats["subdirs"]:
        lineas.extend(imprimir_arbol(sub, indent + 1))
    return lineas


def buscar_carpeta_tfm(base: Path) -> Path | None:
    """Intenta localizar la carpeta raíz del TFM."""
    for candidato in CANDIDATOS_TFM:
        p = base / candidato
        if p.exists() and p.is_dir():
            return p
    # búsqueda parcial un nivel
    try:
        for item in base.iterdir():
            if item.is_dir() and any(c.lower() in item.name.lower() for c in ["tfm", "reconstruccion", "3d"]):
                return item
    except PermissionError:
        pass
    return None


# ── Script principal ──────────────────────────────────────────────────────────

def main():
    lineas_informe = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas_informe.append(f"=" * 70)
    lineas_informe.append(f"  AUDITORÍA DRIVE — TFM Reconstrucción 3D")
    lineas_informe.append(f"  Generado: {ts}")
    lineas_informe.append(f"=" * 70)

    # 1. Localizar carpeta raíz TFM
    carpeta_tfm = buscar_carpeta_tfm(RUTA_BASE)
    if carpeta_tfm is None:
        msg = (
            f"\n⚠️  No se encontró carpeta TFM en {RUTA_BASE}\n"
            f"   Candidatos buscados: {CANDIDATOS_TFM}\n"
            f"   Añade la ruta correcta en CANDIDATOS_TFM al principio del script."
        )
        print(msg)
        lineas_informe.append(msg)
    else:
        lineas_informe.append(f"\n✅  Carpeta TFM: {carpeta_tfm}\n")
        print(f"Analizando {carpeta_tfm} ...")

        stats_tfm = analizar_carpeta(carpeta_tfm, max_depth=5)

        # Árbol
        lineas_informe.append("─" * 70)
        lineas_informe.append("  ÁRBOL DE CARPETAS")
        lineas_informe.append("─" * 70)
        lineas_informe.extend(imprimir_arbol(stats_tfm))

        # Modelos / checkpoints
        todos_modelos = stats_tfm["modelos"]
        lineas_informe.append("\n" + "─" * 70)
        lineas_informe.append(f"  CHECKPOINTS / MODELOS ({len(todos_modelos)} ficheros)")
        lineas_informe.append("─" * 70)
        if todos_modelos:
            for m in sorted(todos_modelos, key=lambda x: -x["tamanyo"]):
                lineas_informe.append(
                    f"  {m['nombre']:<50} {tamanyo_legible(m['tamanyo']):>8}  {m['fecha']}"
                )
                lineas_informe.append(f"    → {m['ruta']}")
        else:
            lineas_informe.append("  (ninguno encontrado)")

        # Datasets
        todos_datos = stats_tfm["datasets"]
        lineas_informe.append("\n" + "─" * 70)
        lineas_informe.append(f"  FICHEROS DE DATOS (.npy/.ply/.obj/.stl)  ({len(todos_datos)})")
        lineas_informe.append("─" * 70)
        if todos_datos:
            ext_count: dict[str, list] = defaultdict(list)
            for d in todos_datos:
                ext_count[Path(d["nombre"]).suffix.lower()].append(d)
            for ext, items in sorted(ext_count.items()):
                total = sum(i["tamanyo"] for i in items)
                lineas_informe.append(
                    f"  {ext}  ×{len(items)}  ({tamanyo_legible(total)} total)"
                )
        else:
            lineas_informe.append("  (ninguno encontrado)")

        # Notebooks
        todos_nb = stats_tfm["notebooks"]
        lineas_informe.append("\n" + "─" * 70)
        lineas_informe.append(f"  NOTEBOOKS ({len(todos_nb)})")
        lineas_informe.append("─" * 70)
        for nb in sorted(todos_nb, key=lambda x: x["fecha"], reverse=True)[:30]:
            lineas_informe.append(f"  {nb['fecha']}  {nb['nombre']}")

        # Resumen global
        lineas_informe.append("\n" + "─" * 70)
        lineas_informe.append("  RESUMEN GLOBAL")
        lineas_informe.append("─" * 70)
        lineas_informe.append(f"  Total ficheros : {stats_tfm['n_ficheros']}")
        lineas_informe.append(f"  Tamaño total   : {tamanyo_legible(stats_tfm['tamanyo_total'])}")
        ext_sorted = sorted(stats_tfm["por_extension"].items(), key=lambda x: -x[1])
        lineas_informe.append("  Por extensión  :")
        for ext, n in ext_sorted[:15]:
            lineas_informe.append(f"    {ext or '(sin ext)':<15} {n:>6} ficheros")

    # Guardar informe
    ruta_informe = RUTA_BASE / "informe_drive_tfm.txt"
    with open(ruta_informe, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas_informe))
    print(f"\nInforme guardado en: {ruta_informe}")
    print("\n".join(lineas_informe))


if __name__ == "__main__":
    main()
