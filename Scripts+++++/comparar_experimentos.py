#!/usr/bin/env python3
"""
Tabla comparativa de todos los experimentos E3.

Lee metricas.json de las carpetas E3/resultados_*/ y combina con los
resultados históricos hardcodeados. Muestra tabla ordenada por CD-L1.

Uso:
    python Scripts/comparar_experimentos.py
    python Scripts/comparar_experimentos.py --csv resultados.csv
    python Scripts/comparar_experimentos.py --solo_completos
"""

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# ── Resultados históricos (no tienen metricas.json local) ──────
HISTORICOS = [
    {
        'version': 'PCN v1',
        'modelo': 'PCN',
        'fecha': '2026-08-04',
        'datasets': ['FB', 'sintetico'],
        'n_pares_total': '~400',
        'n_test': '?',
        'epochs': 500,
        'best_epoch': '?',
        'cd_l1': 0.077,
        'f_score': None,
        'centrar_en_roto': True,
        'notas': 'primer entrenamiento, sin blacklist',
    },
    {
        'version': 'PCN v3',
        'modelo': 'PCN',
        'fecha': '2026-08-10',
        'datasets': ['FB', 'sintetico'],
        'n_pares_total': '~400',
        'n_test': '?',
        'epochs': 500,
        'best_epoch': '?',
        'cd_l1': 0.0665,
        'f_score': 0.024,
        'centrar_en_roto': True,
        'notas': 'A100',
    },
    {
        'version': 'PCN v4',
        'modelo': 'PCN',
        'fecha': '2026-08-12',
        'datasets': ['FB', 'sintetico_v2'],
        'n_pares_total': '~400',
        'n_test': '?',
        'epochs': 500,
        'best_epoch': 480,
        'cd_l1': 0.0641,
        'f_score': 0.0236,
        'centrar_en_roto': True,
        'notas': 'roturas v2 (plano+chip+cuña), A100',
    },
    {
        'version': 'PCN v5',
        'modelo': 'PCN',
        'fecha': '2026-08-15',
        'datasets': ['FB', 'sintetico_v2'],
        'n_pares_total': '~400',
        'n_test': '?',
        'epochs': 500,
        'best_epoch': 445,
        'cd_l1': 0.0630,
        'f_score': 0.0257,
        'centrar_en_roto': True,
        'notas': 'fix centroide (H19)',
    },
    {
        'version': 'PoinTr v2',
        'modelo': 'PoinTr',
        'fecha': '2026-08-24',
        'datasets': ['FB_v1', 'sintetico_filtrado'],
        'n_pares_total': 402,
        'n_test': 41,
        'epochs': 150,
        'best_epoch': 150,
        'cd_l1': 0.0533,
        'f_score': 0.3278,
        'centrar_en_roto': True,
        'notas': 'blacklist 1958 pares; ep1-30 solo FB (contaminacion)',
    },
    {
        'version': 'PoinTr v3',
        'modelo': 'PoinTr',
        'fecha': '2026-08-25',
        'datasets': ['FB_v1', 'sintetico_filtrado'],
        'n_pares_total': 402,
        'n_test': None,
        'epochs': 200,
        'best_epoch': 155,
        'cd_l1': None,
        'f_score': None,
        'centrar_en_roto': False,
        'notas': 'CENTRAR_EN_ROTO=False — evaluacion pendiente',
    },
    {
        'version': 'PoinTr v4',
        'modelo': 'PoinTr',
        'fecha': '2026-08-25',
        'datasets': ['FB_v2'],
        'n_pares_total': 61,
        'n_test': 7,
        'epochs': 300,
        'best_epoch': 285,
        'cd_l1': 0.0569,
        'f_score': 0.0285,
        'centrar_en_roto': False,
        'notas': 'solo FB v2 alineado; test muy pequeño (7 muestras)',
    },
]


def cargar_json_locales():
    """Lee todos los metricas.json en E3/resultados_*/"""
    resultados = []
    for ruta in sorted(BASE.glob('E3/resultados_*/metricas.json')):
        try:
            with open(ruta, encoding='utf-8') as f:
                d = json.load(f)
            resultados.append(d)
        except Exception as e:
            print(f'[WARN] No se pudo leer {ruta}: {e}')
    return resultados


def _fmt(val, decimales=4, sufijo=''):
    if val is None: return '—'
    if isinstance(val, str): return val
    return f'{val:.{decimales}f}{sufijo}'


def _datasets_str(d):
    if isinstance(d, list): return '+'.join(d)
    return str(d)


def imprimir_tabla(filas, solo_completos=False):
    if solo_completos:
        filas = [f for f in filas if f.get('cd_l1') is not None]

    filas_ord = sorted(filas, key=lambda x: (x.get('cd_l1') is None, x.get('cd_l1') or 9999))

    # Anchos de columna
    W = {
        'version':  max(12, max(len(str(f.get('version','')))+1 for f in filas_ord)),
        'modelo':   8,
        'datasets': max(12, max(len(_datasets_str(f.get('datasets','')))+1 for f in filas_ord)),
        'pares':    7,
        'test':     5,
        'ep':       6,
        'best':     6,
        'cd':       8,
        'fs':       8,
        'notas':    40,
    }

    sep = (f"{'─'*W['version']}┼{'─'*W['modelo']}┼{'─'*W['datasets']}┼"
           f"{'─'*W['pares']}┼{'─'*W['test']}┼{'─'*W['ep']}┼{'─'*W['best']}┼"
           f"{'─'*W['cd']}┼{'─'*W['fs']}┼{'─'*W['notas']}")
    cabecera = (f"{'Versión':<{W['version']}}│{'Modelo':<{W['modelo']}}│"
                f"{'Datasets':<{W['datasets']}}│{'Pares':>{W['pares']}}│"
                f"{'Test':>{W['test']}}│{'Ep':>{W['ep']}}│{'Best':>{W['best']}}│"
                f"{'CD-L1':>{W['cd']}}│{'F-Score':>{W['fs']}}│{'Notas':<{W['notas']}}")

    print()
    print('═' * len(sep))
    print('  COMPARATIVA E3 — todos los experimentos')
    print('═' * len(sep))
    print(cabecera)
    print(sep)

    prev_modelo = None
    for f in filas_ord:
        modelo = f.get('modelo', '?')
        if prev_modelo and modelo != prev_modelo:
            print(sep)
        prev_modelo = modelo

        cd  = f.get('cd_l1')
        fs  = f.get('f_score')
        ver = str(f.get('version', '?'))
        ds  = _datasets_str(f.get('datasets', '?'))
        par = _fmt(f.get('n_pares_total'), 0)
        tst = _fmt(f.get('n_test'), 0)
        ep  = _fmt(f.get('epochs'), 0)
        best= _fmt(f.get('best_epoch'), 0)
        nt  = (f.get('notas') or '')[:W['notas']-1]

        cd_str = _fmt(cd)
        fs_str = _fmt(fs)

        # Resaltar si es el mejor CD conocido
        mejor_cd = min((x['cd_l1'] for x in filas_ord if x.get('cd_l1') is not None), default=None)
        marca = ' ★' if cd is not None and cd == mejor_cd else '  '

        print(f"{ver:<{W['version']}}│{modelo:<{W['modelo']}}│{ds:<{W['datasets']}}│"
              f"{par:>{W['pares']}}│{tst:>{W['test']}}│{ep:>{W['ep']}}│{best:>{W['best']}}│"
              f"{cd_str:>{W['cd']}}│{fs_str:>{W['fs']}}│{nt:<{W['notas']}}{marca}")

    print('═' * len(sep))
    print()
    print('  ★ = mejor CD-L1 conocido')
    print('  — = métrica no disponible (evaluación pendiente)')
    print('  Nota: F-Score de PoinTr v2 está inflado (CENTRAR_EN_ROTO=True hacía la tarea más fácil)')
    print()


def guardar_csv(filas, ruta):
    import csv
    campos = ['version','modelo','fecha','datasets','n_pares_total','n_test',
              'epochs','best_epoch','cd_l1','f_score','centrar_en_roto','notas']
    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
        w.writeheader()
        for fila in filas:
            row = dict(fila)
            row['datasets'] = _datasets_str(fila.get('datasets', ''))
            w.writerow(row)
    print(f'CSV guardado: {ruta}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--csv', default=None, help='Guardar también en CSV')
    ap.add_argument('--solo_completos', action='store_true',
                    help='Mostrar solo experimentos con CD-L1 disponible')
    args = ap.parse_args()

    locales = cargar_json_locales()
    versiones_locales = {d.get('version') for d in locales}

    # Combinar: locales tienen prioridad sobre históricos
    historicos_filtrados = [h for h in HISTORICOS if h['version'] not in versiones_locales]
    todos = historicos_filtrados + locales

    if locales:
        print(f'[INFO] {len(locales)} experimentos leídos de E3/resultados_*/metricas.json')
    if historicos_filtrados:
        print(f'[INFO] {len(historicos_filtrados)} experimentos históricos (hardcoded)')

    imprimir_tabla(todos, solo_completos=args.solo_completos)

    if args.csv:
        guardar_csv(todos, args.csv)


if __name__ == '__main__':
    main()
