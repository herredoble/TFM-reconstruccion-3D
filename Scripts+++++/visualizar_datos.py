#!/usr/bin/env python3
"""
Visualizador de pares roto/completo y mallas 3D.

Uso:
    python Scripts/visualizar_datos.py --carpeta Datos/fantastic_breaks/procesado_v2
    python Scripts/visualizar_datos.py --carpeta Datos/fantastic_breaks/procesado
    python Scripts/visualizar_datos.py --carpeta Datos/sintetico_roturas_centradas
    python Scripts/visualizar_datos.py --carpeta Datos/shapenet/limpias/03797390
    python Scripts/visualizar_datos.py --carpeta Datos/shapenet/limpias/03797390 --n 20 --aleatorio

    # Comparar dos carpetas lado a lado (ej. FB v1 vs FB v2):
    python Scripts/visualizar_datos.py --carpeta Datos/fantastic_breaks/procesado \
                                        --comparar Datos/fantastic_breaks/procesado_v2

Controles:
    →  / Enter / Espacio : siguiente
    ←                    : anterior
    q  / Esc             : salir
    g                    : guardar imagen actual en <carpeta>/vis/
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

matplotlib.rcParams['toolbar'] = 'None'

AZUL   = '#1565C0'
ROJO   = '#C62828'
VERDE  = '#2E7D32'
NARANJA = '#E65100'


# ── Carga ──────────────────────────────────────────────────────

def cargar_par_npy(stem, carpeta):
    ruta_r = carpeta / f'{stem}_roto.npy'
    ruta_c = carpeta / f'{stem}_completo.npy'
    roto     = np.load(ruta_r).astype(np.float32) if ruta_r.exists() else None
    completo = np.load(ruta_c).astype(np.float32) if ruta_c.exists() else None
    return roto, completo


def cargar_ply(ruta, n_puntos=2048):
    try:
        import trimesh
        m = trimesh.load(str(ruta), force='mesh')
        pts = np.array(m.sample(n_puntos), dtype=np.float32)
        return None, pts
    except Exception as e:
        print(f'[WARN] {Path(ruta).name}: {e}')
        return None, None


# ── Dibujo ─────────────────────────────────────────────────────

def _scatter3(ax, pts, color, alpha, s, label=None):
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
               s=s, c=color, alpha=alpha, label=label, depthshade=True)


def _scatter2(ax, pts, ix, iy, color, alpha, s):
    ax.scatter(pts[:, ix], pts[:, iy], s=s, c=color, alpha=alpha)


def dibujar(axes, roto, completo, roto2, completo2, titulo):
    ax3, axy, axz, ayz = axes
    for ax in axes:
        ax.cla()

    if completo is not None:
        _scatter3(ax3, completo, AZUL, 0.3, 1, 'completo')
        _scatter2(axy, completo, 0, 1, AZUL, 0.3, 1)
        _scatter2(axz, completo, 0, 2, AZUL, 0.3, 1)
        _scatter2(ayz, completo, 1, 2, AZUL, 0.3, 1)

    if roto is not None:
        _scatter3(ax3, roto, ROJO, 0.7, 2, 'roto')
        _scatter2(axy, roto, 0, 1, ROJO, 0.7, 2)
        _scatter2(axz, roto, 0, 2, ROJO, 0.7, 2)
        _scatter2(ayz, roto, 1, 2, ROJO, 0.7, 2)

    # Segunda carpeta (comparar)
    if completo2 is not None:
        _scatter3(ax3, completo2, VERDE, 0.25, 1, 'completo v2')
    if roto2 is not None:
        _scatter3(ax3, roto2, NARANJA, 0.6, 2, 'roto v2')

    ax3.set_title(titulo, fontsize=8)
    if roto is not None or completo2 is not None:
        ax3.legend(loc='upper right', markerscale=4, fontsize=6)

    axy.set_title('XY — vista superior', fontsize=8)
    axz.set_title('XZ — vista frontal',  fontsize=8)
    ayz.set_title('YZ — vista lateral',  fontsize=8)
    for ax, (xl, yl) in zip((axy, axz, ayz),
                             (('X', 'Y'), ('X', 'Z'), ('Y', 'Z'))):
        ax.set_xlabel(xl, fontsize=7); ax.set_ylabel(yl, fontsize=7)
        ax.set_aspect('equal', 'box')
        ax.tick_params(labelsize=6)


def estadisticas(stem, roto, completo, idx, total):
    print(f'\n[{idx+1}/{total}] {stem}')
    if roto is not None:
        print(f'  roto    : {roto.shape}  '
              f'min={roto.min(0).round(3)}  max={roto.max(0).round(3)}  '
              f'centroide={roto.mean(0).round(3)}')
    if completo is not None:
        print(f'  completo: {completo.shape}  '
              f'min={completo.min(0).round(3)}  max={completo.max(0).round(3)}  '
              f'centroide={completo.mean(0).round(3)}')
    if roto is not None and completo is not None:
        desp = np.linalg.norm(roto.mean(0) - completo.mean(0))
        overlap = _overlap(roto, completo)
        print(f'  desplazamiento centroide roto↔completo : {desp:.4f}')
        print(f'  puntos roto a <0.05 del completo       : {overlap:.1%}')
        if desp > 0.5:
            print('  ⚠️  POSIBLE DESALINEACION — centroide muy separado')


def _overlap(roto, completo, umbral=0.05):
    from scipy.spatial import KDTree
    tree = KDTree(completo)
    dists, _ = tree.query(roto, k=1)
    return (dists < umbral).mean()


# ── Main ───────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--carpeta',  required=True, help='Carpeta principal')
    ap.add_argument('--comparar', default=None,  help='Segunda carpeta (comparación lado a lado)')
    ap.add_argument('--n',        type=int, default=0, help='Cuántos pares (0=todos)')
    ap.add_argument('--aleatorio', action='store_true')
    ap.add_argument('--desde',    type=int, default=0, help='Empezar por el índice N')
    args = ap.parse_args()

    carpeta  = Path(args.carpeta)
    carpeta2 = Path(args.comparar) if args.comparar else None

    if not carpeta.exists():
        print(f'ERROR: no existe: {carpeta}'); sys.exit(1)

    # Detectar modo
    npy_compl = sorted(carpeta.glob('*_completo.npy'))
    ply_files  = sorted(carpeta.rglob('*.ply'))

    if npy_compl:
        modo  = 'npy'
        stems = [p.stem.replace('_completo', '') for p in npy_compl]
        print(f'Modo .npy — {len(stems)} pares en {carpeta}')
    elif ply_files:
        modo  = 'ply'
        stems = [str(p) for p in ply_files]
        print(f'Modo .ply — {len(stems)} archivos en {carpeta}')
    else:
        print('ERROR: no se encontraron *_completo.npy ni *.ply'); sys.exit(1)

    if args.aleatorio:
        random.shuffle(stems)
    if args.n > 0:
        stems = stems[:args.n]

    print('Controles: → / Enter / Espacio = siguiente | ← = anterior | q = salir | g = guardar')

    fig = plt.figure(figsize=(14, 8))
    ax3 = fig.add_subplot(221, projection='3d')
    axy = fig.add_subplot(222)
    axz = fig.add_subplot(223)
    ayz = fig.add_subplot(224)
    axes = (ax3, axy, axz, ayz)

    titulo_base = carpeta.name
    if carpeta2:
        titulo_base += f'  vs  {carpeta2.name}'
    fig.suptitle(f'{titulo_base}   [← → navegar  |  q salir  |  g guardar]', fontsize=9)

    idx   = [max(0, args.desde)]
    salir = [False]

    def cargar(i):
        s = stems[i]
        if modo == 'npy':
            roto, completo = cargar_par_npy(s, carpeta)
            roto2, completo2 = (cargar_par_npy(s, carpeta2)
                                if carpeta2 and (carpeta2 / f'{s}_completo.npy').exists()
                                else (None, None))
            titulo = f'[{i+1}/{len(stems)}]  {s}'
        else:
            roto, completo = cargar_ply(s)
            roto2, completo2 = None, None
            titulo = f'[{i+1}/{len(stems)}]  {Path(s).name}'
        return roto, completo, roto2, completo2, titulo, s

    def mostrar(i):
        roto, completo, roto2, completo2, titulo, s = cargar(i)
        if completo is None and roto is None:
            print(f'  [!] sin datos: {s}')
            return
        dibujar(axes, roto, completo, roto2, completo2, titulo)
        estadisticas(s, roto, completo, i, len(stems))
        fig.canvas.draw_idle()

    def guardar_img(i):
        vis_dir = carpeta / 'vis'; vis_dir.mkdir(exist_ok=True)
        nombre  = f'{i:04d}_{Path(stems[i]).stem}.png'
        fig.savefig(vis_dir / nombre, dpi=100, bbox_inches='tight')
        print(f'  Guardado: {vis_dir / nombre}')

    def on_key(event):
        if event.key in ('q', 'escape'):
            salir[0] = True
            plt.close('all')
        elif event.key in ('right', 'enter', ' '):
            if idx[0] < len(stems) - 1:
                idx[0] += 1
                mostrar(idx[0])
            else:
                print('  (último par)')
        elif event.key == 'left':
            if idx[0] > 0:
                idx[0] -= 1
                mostrar(idx[0])
        elif event.key == 'g':
            guardar_img(idx[0])

    fig.canvas.mpl_connect('key_press_event', on_key)
    mostrar(idx[0])
    plt.tight_layout()
    plt.show()
    print('Fin.')


if __name__ == '__main__':
    main()
