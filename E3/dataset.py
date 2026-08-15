# -*- coding: utf-8 -*-
"""
Data loader para el modelo de reparación E3 (shape completion).

QUÉ HACE
  Lee pares (roto.npy, completo.npy) de una o varias carpetas,
  los divide en train/val/test, y devuelve DataLoaders de PyTorch.

CÓMO SE USA (desde el script de entrenamiento)
  from E3.dataset import construir_dataloaders

  train_loader, val_loader, test_loader = construir_dataloaders(
      carpetas=[
          "Datos/fantastic_breaks/procesado",
          "Datos/sintetico/roturas",
      ],
      batch_size=32,
      augmentar=True,
  )

  for roto, completo in train_loader:
      # roto    → tensor (batch, 2048, 3)  — entrada al modelo
      # completo → tensor (batch, 2048, 3) — target (lo que el modelo debe predecir)
      ...

FORMATO DE ARCHIVOS ESPERADO
  Cualquier carpeta con archivos .npy que sigan la convención:
    <prefijo>_completo.npy   shape (2048, 3) float32
    <prefijo>_roto.npy       shape (2048, 3) float32
  Los dos archivos del mismo par tienen el mismo prefijo.
"""

import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

# ---------------------------------------------------------------------------
# FILTRO DE OUTLIERS
# Activo por defecto. Para desactivarlo, pon FILTRAR_OUTLIERS = False.
#
# Contexto: los .npy se generaron con plyfile, que lee todos los vértices del
# .ply sin separar componentes conectados. Algunos modelos tienen artefactos
# flotantes (asas sueltas, fragmentos desconectados). El filtro elimina puntos
# que están a más de SIGMA desviaciones estándar del centroide en cualquier
# eje, y luego vuelve a muestrear hasta N_PUNTOS para mantener el shape fijo.
#
# Impacto medido sobre 500 pares aleatorios:
#   Sin outliers (0%)       : 63.6%  → el filtro no cambia nada
#   Outliers leves (<5%)    : 24.0%  → limpieza mínima
#   Outliers medios (5-15%) : 12.4%  → limpieza visible
#   Outliers graves (≥15%)  :  0.0%  → no hay casos extremos
# ---------------------------------------------------------------------------
FILTRAR_OUTLIERS = True   # ← cambia a False para desactivar
SIGMA_OUTLIERS   = 2.5    # umbral: puntos a más de 2.5σ del centroide se eliminan
N_PUNTOS         = 2048   # puntos por nube tras el filtro (debe coincidir con el modelo)

# ---------------------------------------------------------------------------
# CENTRADO EN EL FRAME DEL FRAGMENTO
# Activo por defecto desde v5. Para desactivarlo, pon CENTRAR_EN_ROTO = False.
#
# Problema (H19): al eliminar 15-50% de puntos de un lado del objeto, el
# centroide de la nube rota se desplaza hacia la región intacta mientras el
# GT permanece en el origen (0,0,0). El modelo tiene que aprender la traslación
# implícitamente → colapsa a placa plana en los peores casos (CD≈0.18-0.23).
#
# Fix: centrar la rota en su propio centroide y desplazar el GT la misma cantidad.
# Ambas nubes quedan en el mismo frame de referencia (centrado en el fragmento).
# En inferencia: centrar el fragmento → predecir → la salida ya está alineada.
# Estándar en FoldingNet, GRNet y la mayoría de implementaciones de shape completion.
# ---------------------------------------------------------------------------
CENTRAR_EN_ROTO = True    # ← cambia a False para comportamiento pre-v5


# ---------------------------------------------------------------------------
# PARTE 0: FILTRO DE OUTLIERS
# ---------------------------------------------------------------------------

def _quitar_outliers_y_remuestrear(
    pts: np.ndarray,
    rng: np.random.Generator,
    sigma: float = SIGMA_OUTLIERS,
    n: int = N_PUNTOS,
) -> np.ndarray:
    """Elimina outliers estadísticos y devuelve exactamente n puntos.

    1. Calcula la media y std por eje (x, y, z).
    2. Descarta los puntos que se alejan más de sigma·std en cualquier eje.
    3. Vuelve a muestrear hasta n puntos (con reemplazo si quedan menos de n).

    Si queda menos de 10% de los puntos tras el filtro, devuelve los originales
    sin filtrar (caso muy raro — evita destruir pares con geometría legítima extrema).
    """
    mean = pts.mean(axis=0)
    std  = pts.std(axis=0).clip(min=1e-6)
    mask = np.all(np.abs(pts - mean) <= sigma * std, axis=1)

    pts_filtrados = pts[mask]
    if len(pts_filtrados) < n * 0.10:
        pts_filtrados = pts  # fallback: sin filtro

    idx = rng.choice(len(pts_filtrados), n, replace=len(pts_filtrados) < n)
    return pts_filtrados[idx].astype(np.float32)


# ---------------------------------------------------------------------------
# PARTE 1: ENCONTRAR LOS PARES EN DISCO
# ---------------------------------------------------------------------------

def construir_pares(carpetas: list[str | Path]) -> list[tuple[Path, Path]]:
    """Escanea las carpetas y devuelve una lista de pares (roto_path, completo_path).

    Lógica:
      - Busca todos los archivos que terminan en '_completo.npy'
      - Para cada uno, deriva la ruta del '_roto.npy' correspondiente
        (mismo nombre, mismo directorio, solo cambia el sufijo)
      - Descarta los pares incompletos (si falta uno de los dos archivos)

    Esto funciona tanto para Fantastic Breaks procesado como para los sintéticos,
    porque ambos siguen la misma convención de nombres.
    """
    pares = []
    omitidos = 0

    for carpeta in carpetas:
        carpeta = Path(carpeta)
        if not carpeta.exists():
            print(f"[AVISO] Carpeta no encontrada, ignorada: {carpeta}")
            continue

        # Buscar todos los archivos completo en esta carpeta
        archivos_completo = sorted(carpeta.glob("*_completo.npy"))

        for ruta_completo in archivos_completo:
            # Derivar la ruta del roto: mismo directorio, mismo stem sin '_completo', más '_roto'
            # Ejemplo: 'shapenet_abc123_completo.npy' → 'shapenet_abc123_roto.npy'
            stem_base = ruta_completo.stem.replace("_completo", "")
            ruta_roto = ruta_completo.parent / f"{stem_base}_roto.npy"

            if not ruta_roto.exists():
                omitidos += 1
                continue

            pares.append((ruta_roto, ruta_completo))

    if omitidos > 0:
        print(f"[AVISO] {omitidos} pares incompletos descartados (falta el _roto.npy)")

    return pares


# ---------------------------------------------------------------------------
# PARTE 2: AUGMENTACIÓN
# Transformaciones aleatorias que se aplican durante el entrenamiento.
# ---------------------------------------------------------------------------

def _rotar_eje_z(pts: np.ndarray, angulo_rad: float) -> np.ndarray:
    """Rota una nube de puntos alrededor del eje Z (eje vertical) en 3D.

    Eje Z = el eje que apunta hacia arriba. Para vasijas es el eje de simetría
    natural: una taza girada 45° sigue siendo la misma taza.

    La matriz de rotación 3×3 para el eje Z es:
      [ cos θ  -sin θ   0 ]
      [ sin θ   cos θ   0 ]
      [  0       0      1 ]

    pts tiene shape (N, 3) → devuelve shape (N, 3)
    """
    c, s = np.cos(angulo_rad), np.sin(angulo_rad)
    # Matriz 3×3 de rotación alrededor de Z
    R = np.array([
        [ c, -s,  0],
        [ s,  c,  0],
        [ 0,  0,  1],
    ], dtype=np.float32)
    # pts.T tiene shape (3, N) → R @ pts.T tiene shape (3, N) → transponer → (N, 3)
    return (R @ pts.T).T


def _augmentar_par(
    roto: np.ndarray,
    completo: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Aplica la misma transformación aleatoria a roto y completo.

    Aplicar la MISMA transformación a los dos es crítico:
    el par (roto, completo) debe seguir siendo coherente después de la augmentación.
    Si rotáramos cada uno por separado, el modelo intentaría aprender a predecir
    una orientación completamente diferente a la entrada — no aprendería nada útil.

    Transformaciones aplicadas:
      1. Rotación aleatoria en Z: ángulo uniforme entre 0° y 360°
      2. Jitter: ruido gaussiano pequeño (σ=0.01) para simular imprecisión del escáner
    """
    # 1. Rotación aleatoria en el eje Z (0 a 360°)
    angulo = rng.uniform(0, 2 * np.pi)
    roto    = _rotar_eje_z(roto,    angulo)
    completo = _rotar_eje_z(completo, angulo)

    # 2. Jitter: ruido gaussiano pequeño
    #    σ=0.01 es estándar en los papers de shape completion
    #    Se aplica solo a roto (la entrada), no al completo (el target debe ser exacto)
    ruido = rng.normal(0, 0.01, roto.shape).astype(np.float32)
    roto = roto + ruido

    return roto, completo


# ---------------------------------------------------------------------------
# PARTE 3: CLASE DATASET
# La clase que PyTorch necesita para gestionar los datos.
# ---------------------------------------------------------------------------

class ShapeCompletionDataset(Dataset):
    """Dataset de PyTorch para shape completion de nubes de puntos.

    PyTorch requiere que cualquier dataset implemente exactamente dos métodos:
      - __len__:     cuántos ejemplos hay
      - __getitem__: dame el ejemplo número i

    El DataLoader llama a estos métodos internamente — tú no los llamas directamente.
    Lo que recibes del DataLoader es un batch de N ejemplos ya apilados en tensores.
    """

    def __init__(
        self,
        pares: list[tuple[Path, Path]],
        augmentar: bool = False,
        semilla: int | None = None,
    ):
        """
        pares:     lista de (roto_path, completo_path) generada por construir_pares()
        augmentar: si True, aplica rotación aleatoria y jitter en cada acceso
        semilla:   semilla del RNG (None = aleatoria, útil para reproducibilidad en val/test)
        """
        self.pares = pares
        self.augmentar = augmentar
        # Cada dataset tiene su propio generador de números aleatorios
        # Así train (semilla None) varía cada época, pero val/test son siempre iguales
        self.rng = np.random.default_rng(semilla)

    def __len__(self) -> int:
        """PyTorch llama a esto para saber cuántos batches preparar."""
        return len(self.pares)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """PyTorch llama a esto N veces por batch para recopilar ejemplos.

        idx: índice del par a cargar (0 a len-1)
        Devuelve: (roto, completo) como tensores float32 de shape (2048, 3)
        """
        ruta_roto, ruta_completo = self.pares[idx]

        # Cargar arrays numpy desde disco
        # np.load es rápido para archivos .npy (formato binario nativo de numpy)
        roto     = np.load(str(ruta_roto))      # shape (2048, 3), float32
        completo = np.load(str(ruta_completo))  # shape (2048, 3), float32

        # Filtro de outliers (ver constante FILTRAR_OUTLIERS al inicio del módulo)
        # Se aplica a ambas nubes para eliminar artefactos flotantes del .ply fuente.
        # El remuestreo posterior garantiza que la shape sigue siendo (2048, 3).
        if FILTRAR_OUTLIERS:
            roto     = _quitar_outliers_y_remuestrear(roto,     self.rng)
            completo = _quitar_outliers_y_remuestrear(completo, self.rng)

        # Centrado en el frame del fragmento (ver constante CENTRAR_EN_ROTO).
        # Se hace ANTES de la augmentación para que la rotación se aplique
        # ya con ambas nubes en el mismo frame de referencia.
        if CENTRAR_EN_ROTO:
            roto_mean = roto.mean(axis=0)
            roto      = roto      - roto_mean
            completo  = completo  - roto_mean

        # Augmentación solo durante entrenamiento
        if self.augmentar:
            roto, completo = _augmentar_par(roto, completo, self.rng)

        # Convertir a tensores de PyTorch
        # torch.from_numpy comparte memoria con el array numpy (sin copia) → eficiente
        return torch.from_numpy(roto.copy()), torch.from_numpy(completo.copy())


# ---------------------------------------------------------------------------
# PARTE 4: FUNCIÓN PRINCIPAL — construir_dataloaders
# Lo que importa el script de entrenamiento.
# ---------------------------------------------------------------------------

def construir_dataloaders(
    carpetas: list[str | Path],
    batch_size: int = 32,
    split: tuple[float, float, float] = (0.8, 0.1, 0.1),
    augmentar: bool = True,
    semilla: int = 42,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Construye los tres DataLoaders (train, val, test) a partir de las carpetas de datos.

    Parámetros:
      carpetas:    lista de directorios con pares _completo.npy / _roto.npy
      batch_size:  ejemplos por batch (32 es estándar para shape completion)
      split:       fracción para (train, val, test) — deben sumar 1.0
      augmentar:   si True, el train loader aplica rotación + jitter
      semilla:     para reproducibilidad del shuffle y el split
      num_workers: subprocesos de carga (0 = carga en el proceso principal; en Windows
                   es mejor dejarlo en 0 para evitar problemas de multiproceso)

    Devuelve:
      (train_loader, val_loader, test_loader)

    Ejemplo de uso en el script de entrenamiento:
      train_loader, val_loader, _ = construir_dataloaders(
          carpetas=["Datos/fantastic_breaks/procesado", "Datos/sintetico/roturas"],
          batch_size=32,
      )
      for roto, completo in train_loader:
          # roto:     (32, 2048, 3)
          # completo: (32, 2048, 3)
          ...
    """
    assert abs(sum(split) - 1.0) < 1e-6, "split debe sumar 1.0"

    # 1. Recopilar todos los pares de todas las carpetas
    todos_los_pares = construir_pares(carpetas)
    n_total = len(todos_los_pares)

    if n_total == 0:
        raise ValueError(
            "No se encontraron pares en las carpetas indicadas. "
            "Comprueba que las rutas son correctas y que los archivos "
            "siguen la convención *_completo.npy / *_roto.npy"
        )

    # 2. Barajar con semilla fija para que el split sea siempre el mismo
    rng = random.Random(semilla)
    rng.shuffle(todos_los_pares)

    # 3. Calcular tamaños de cada split
    n_train = int(split[0] * n_total)
    n_val   = int(split[1] * n_total)
    # Test se lleva el resto para que sumen exactamente n_total
    n_test  = n_total - n_train - n_val

    pares_train = todos_los_pares[:n_train]
    pares_val   = todos_los_pares[n_train : n_train + n_val]
    pares_test  = todos_los_pares[n_train + n_val :]

    print(f"\n=== Dataset E3 ===")
    print(f"  Total pares    : {n_total}")
    print(f"  Train          : {len(pares_train)} ({len(pares_train)/n_total:.0%})")
    print(f"  Val            : {len(pares_val)}   ({len(pares_val)/n_total:.0%})")
    print(f"  Test           : {len(pares_test)}  ({len(pares_test)/n_total:.0%})")
    print(f"  Batch size     : {batch_size}")
    print(f"  Augmentación   : {augmentar}")

    # 4. Crear los tres datasets
    #    Solo train tiene augmentación — val y test deben ser deterministas
    ds_train = ShapeCompletionDataset(pares_train, augmentar=augmentar, semilla=None)
    ds_val   = ShapeCompletionDataset(pares_val,   augmentar=False,     semilla=0)
    ds_test  = ShapeCompletionDataset(pares_test,  augmentar=False,     semilla=0)

    # 5. Crear los DataLoaders
    #    shuffle=True en train: baraja los pares en cada época
    #    shuffle=False en val/test: el orden no importa y es más reproducible
    train_loader = DataLoader(ds_train, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=True)
    val_loader   = DataLoader(ds_val,   batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=True)
    test_loader  = DataLoader(ds_test,  batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=True)

    return train_loader, val_loader, test_loader


# ---------------------------------------------------------------------------
# TEST RÁPIDO — ejecutar directamente para verificar que funciona
# python E3/dataset.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pathlib import Path

    BASE_DIR = Path(r"C:\edf\tfm")
    carpetas = [
        BASE_DIR / "Datos" / "fantastic_breaks" / "procesado",
        BASE_DIR / "Datos" / "sintetico" / "roturas",
    ]

    train_loader, val_loader, test_loader = construir_dataloaders(
        carpetas=carpetas,
        batch_size=32,
        augmentar=True,
    )

    print("\n--- Primer batch de train ---")
    roto, completo = next(iter(train_loader))
    print(f"  roto.shape    : {roto.shape}     dtype: {roto.dtype}")
    print(f"  completo.shape: {completo.shape}  dtype: {completo.dtype}")
    print(f"  roto min/max  : {roto.min():.3f} / {roto.max():.3f}")
    print(f"  completo min/max: {completo.min():.3f} / {completo.max():.3f}")
    print(f"\n  Batches en train : {len(train_loader)}")
    print(f"  Batches en val   : {len(val_loader)}")
    print(f"  Batches en test  : {len(test_loader)}")
    print("\nOK — el data loader funciona correctamente.")
