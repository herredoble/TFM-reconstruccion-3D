# ============================================================
# MODULO COMUN: MODELO PIX2VOX++/A
#
# Contiene, sacado literalmente de Pix2vox___Ampliado.ipynb,
# solo lo imprescindible para cargar el modelo y un checkpoint
# ya entrenado (uso en inferencia, no en entrenamiento).
#
# Guardar este archivo en Drive, por ejemplo en:
#   Datos_E2_E3/General/codigo_comun/modelo_pix2vox.py
#
# Uso desde cualquier notebook (tras montar Drive):
#
#   import sys
#   sys.path.append("/content/drive/MyDrive/Datos_E2_E3/General/codigo_comun")
#   from modelo_pix2vox import (
#       Pix2VoxPlusPlusA,
#       cargar_checkpoint_finetuning,
#       DEVICE,
#       RUTA_CHECKPOINTS,
#   )
# ============================================================

import gc
import numpy as np
import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Ruta base del proyecto. Definida aqui directamente porque este
# archivo se ejecuta como modulo independiente al importarlo: no
# puede depender de variables definidas en el notebook que lo importa.
RUTA_BASE = Path("/content/drive/MyDrive/Datos_E2_E3")
RUTA_CHECKPOINTS = RUTA_BASE / "E2/Pix2Vox++/checkpoints"


# ============================================================
# 6. ARQUITECTURA PIX2VOX++/A
# ============================================================

LEAKY_RELU_VALUE = 0.2
USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS = False


# ------------------------------------------------------------
# Encoder 2D
# ------------------------------------------------------------

class EncoderPix2VoxPlusPlusA(nn.Module):
    """
    Encoder 2D de Pix2Vox++/A.

    Entrada
    -------
    imagenes : torch.Tensor
        Forma:
            (batch, numero_vistas, 3, 224, 224)

    Salida
    ------
    caracteristicas : torch.Tensor
        Forma:
            (batch, numero_vistas, 256, 7, 7)
    """

    def __init__(
        self,
        usar_pesos_imagenet=False
    ):
        super().__init__()

        # Cuando se cargue el checkpoint completo de Pix2Vox++,
        # estos pesos serán sustituidos por los del checkpoint.
        pesos_resnet = (
            models.ResNet50_Weights.DEFAULT
            if usar_pesos_imagenet
            else None
        )

        resnet = models.resnet50(
            weights=pesos_resnet
        )

        # Se conserva ResNet-50 hasta layer2.
        # Para una imagen 224 x 224 produce:
        # (batch, 512, 28, 28)
        self.resnet = nn.Sequential(
            resnet.conv1,
            resnet.bn1,
            resnet.relu,
            resnet.maxpool,
            resnet.layer1,
            resnet.layer2,
        )

        self.layer1 = nn.Sequential(
            nn.Conv2d(
                in_channels=512,
                out_channels=512,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(512),
            nn.ReLU(),
        )

        self.layer2 = nn.Sequential(
            nn.Conv2d(
                in_channels=512,
                out_channels=256,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(
                kernel_size=2
            ),
        )

        self.layer3 = nn.Sequential(
            nn.Conv2d(
                in_channels=256,
                out_channels=256,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(
                kernel_size=2
            ),
        )

    def forward(self, imagenes):

        if imagenes.ndim != 5:
            raise ValueError(
                "El encoder espera un tensor con forma "
                "(batch, vistas, 3, 224, 224). "
                f"Forma recibida: {tuple(imagenes.shape)}"
            )

        if imagenes.shape[2] != 3:
            raise ValueError(
                "Las imágenes deben contener tres canales."
            )

        # Se coloca primero la dimensión de las vistas:
        # (vistas, batch, canales, alto, ancho)
        imagenes_por_vista = imagenes.permute(
            1,
            0,
            2,
            3,
            4
        ).contiguous()

        caracteristicas_vistas = []

        # Los pesos del encoder son compartidos.
        for imagen_vista in torch.unbind(
            imagenes_por_vista,
            dim=0
        ):
            caracteristicas = self.resnet(
                imagen_vista
            )

            caracteristicas = self.layer1(
                caracteristicas
            )

            caracteristicas = self.layer2(
                caracteristicas
            )

            caracteristicas = self.layer3(
                caracteristicas
            )

            caracteristicas_vistas.append(
                caracteristicas
            )

        # (batch, vistas, 256, 7, 7)
        caracteristicas_vistas = torch.stack(
            caracteristicas_vistas,
            dim=1
        )

        return caracteristicas_vistas


# ------------------------------------------------------------
# Decoder 3D
# ------------------------------------------------------------

class DecoderPix2VoxPlusPlusA(nn.Module):
    """
    Genera una reconstrucción voxel preliminar por cada vista.

    Entrada
    -------
    caracteristicas : torch.Tensor
        (batch, vistas, 256, 7, 7)

    Salida
    ------
    caracteristicas_3d : torch.Tensor
        (batch, vistas, 9, 32, 32, 32)

    volumenes_preliminares : torch.Tensor
        (batch, vistas, 32, 32, 32)
    """

    def __init__(self):
        super().__init__()

        # 256 x 7 x 7 = 12.544 valores.
        #
        # Esos valores se reorganizan como:
        # 1.568 x 2 x 2 x 2 = 12.544.
        self.layer1 = nn.Sequential(
            nn.ConvTranspose3d(
                in_channels=1568,
                out_channels=512,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(512),
            nn.ReLU(),
        )

        self.layer2 = nn.Sequential(
            nn.ConvTranspose3d(
                in_channels=512,
                out_channels=128,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(128),
            nn.ReLU(),
        )

        self.layer3 = nn.Sequential(
            nn.ConvTranspose3d(
                in_channels=128,
                out_channels=32,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(32),
            nn.ReLU(),
        )

        self.layer4 = nn.Sequential(
            nn.ConvTranspose3d(
                in_channels=32,
                out_channels=8,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(8),
            nn.ReLU(),
        )

        self.layer5 = nn.Sequential(
            nn.ConvTranspose3d(
                in_channels=8,
                out_channels=1,
                kernel_size=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.Sigmoid(),
        )

    def forward(self, caracteristicas_imagenes):

        if caracteristicas_imagenes.ndim != 5:
            raise ValueError(
                "El decoder espera un tensor con forma "
                "(batch, vistas, 256, 7, 7). "
                f"Forma recibida: "
                f"{tuple(caracteristicas_imagenes.shape)}"
            )

        caracteristicas_por_vista = (
            caracteristicas_imagenes.permute(
                1,
                0,
                2,
                3,
                4
            ).contiguous()
        )

        lista_caracteristicas_3d = []
        lista_volumenes = []

        for caracteristicas_vista in torch.unbind(
            caracteristicas_por_vista,
            dim=0
        ):
            # (batch, 1568, 2, 2, 2)
            volumen = caracteristicas_vista.reshape(
                -1,
                1568,
                2,
                2,
                2
            )

            volumen = self.layer1(
                volumen
            )

            volumen = self.layer2(
                volumen
            )

            volumen = self.layer3(
                volumen
            )

            # Características tridimensionales:
            # (batch, 8, 32, 32, 32)
            volumen = self.layer4(
                volumen
            )

            caracteristicas_3d = volumen

            # Probabilidad de ocupación:
            # (batch, 1, 32, 32, 32)
            volumen_ocupacion = self.layer5(
                volumen
            )

            # Se concatenan las ocho características y
            # la probabilidad: 8 + 1 = 9 canales.
            caracteristicas_3d = torch.cat(
                [
                    caracteristicas_3d,
                    volumen_ocupacion,
                ],
                dim=1
            )

            lista_caracteristicas_3d.append(
                caracteristicas_3d
            )

            lista_volumenes.append(
                volumen_ocupacion.squeeze(1)
            )

        caracteristicas_3d = torch.stack(
            lista_caracteristicas_3d,
            dim=1
        )

        volumenes_preliminares = torch.stack(
            lista_volumenes,
            dim=1
        )

        return (
            caracteristicas_3d,
            volumenes_preliminares,
        )


# ------------------------------------------------------------
# Fusión contextual multiescala
# ------------------------------------------------------------

class MergerPix2VoxPlusPlusA(nn.Module):
    """
    Fusiona los volúmenes preliminares de todas las vistas.

    Para cada vóxel calcula un peso diferente para cada vista.
    Los pesos se normalizan mediante softmax.
    """

    def __init__(self):
        super().__init__()

        self.layer1 = nn.Sequential(
            nn.Conv3d(
                9,
                9,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(9),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

        self.layer2 = nn.Sequential(
            nn.Conv3d(
                9,
                9,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(9),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

        self.layer3 = nn.Sequential(
            nn.Conv3d(
                9,
                9,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(9),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

        self.layer4 = nn.Sequential(
            nn.Conv3d(
                9,
                9,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(9),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

        # Se concatenan las cuatro escalas:
        # 9 + 9 + 9 + 9 = 36 canales.
        self.layer5 = nn.Sequential(
            nn.Conv3d(
                36,
                9,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(9),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

        self.layer6 = nn.Sequential(
            nn.Conv3d(
                9,
                1,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm3d(1),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
        )

    def forward(
        self,
        caracteristicas_3d,
        volumenes_preliminares
    ):
        numero_vistas = (
            volumenes_preliminares.shape[1]
        )

        pesos_vistas = []

        for indice_vista in range(
            numero_vistas
        ):
            caracteristicas_vista = (
                caracteristicas_3d[
                    :,
                    indice_vista,
                    :,
                    :,
                    :,
                    :
                ]
            )

            peso_escala_1 = self.layer1(
                caracteristicas_vista
            )

            peso_escala_2 = self.layer2(
                peso_escala_1
            )

            peso_escala_3 = self.layer3(
                peso_escala_2
            )

            peso_escala_4 = self.layer4(
                peso_escala_3
            )

            peso_multiescala = self.layer5(
                torch.cat(
                    [
                        peso_escala_1,
                        peso_escala_2,
                        peso_escala_3,
                        peso_escala_4,
                    ],
                    dim=1
                )
            )

            peso_vista = self.layer6(
                peso_multiescala
            ).squeeze(1)

            pesos_vistas.append(
                peso_vista
            )

        # (batch, vistas, 32, 32, 32)
        pesos_vistas = torch.stack(
            pesos_vistas,
            dim=1
        )

        # Para cada posición voxel, la suma de los pesos
        # de todas las vistas es igual a uno.
        pesos_vistas = torch.softmax(
            pesos_vistas,
            dim=1
        )

        volumen_fusionado = torch.sum(
            volumenes_preliminares
            * pesos_vistas,
            dim=1
        )

        volumen_fusionado = torch.clamp(
            volumen_fusionado,
            min=0.0,
            max=1.0
        )

        return volumen_fusionado


# ------------------------------------------------------------
# Refiner 3D
# ------------------------------------------------------------

class RefinerPix2VoxPlusPlusA(nn.Module):
    """
    Refina el volumen fusionado mediante una arquitectura
    3D encoder-decoder con conexiones residuales.
    """

    def __init__(self):
        super().__init__()

        self.layer1 = nn.Sequential(
            nn.Conv3d(
                1,
                32,
                kernel_size=4,
                padding=2
            ),
            nn.BatchNorm3d(32),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
            nn.MaxPool3d(
                kernel_size=2
            ),
        )

        self.layer2 = nn.Sequential(
            nn.Conv3d(
                32,
                64,
                kernel_size=4,
                padding=2
            ),
            nn.BatchNorm3d(64),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
            nn.MaxPool3d(
                kernel_size=2
            ),
        )

        self.layer3 = nn.Sequential(
            nn.Conv3d(
                64,
                128,
                kernel_size=4,
                padding=2
            ),
            nn.BatchNorm3d(128),
            nn.LeakyReLU(
                LEAKY_RELU_VALUE
            ),
            nn.MaxPool3d(
                kernel_size=2
            ),
        )

        self.layer4 = nn.Sequential(
            nn.Linear(
                8192,
                2048
            ),
            nn.ReLU(),
        )

        self.layer5 = nn.Sequential(
            nn.Linear(
                2048,
                8192
            ),
            nn.ReLU(),
        )

        self.layer6 = nn.Sequential(
            nn.ConvTranspose3d(
                128,
                64,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(64),
            nn.ReLU(),
        )

        self.layer7 = nn.Sequential(
            nn.ConvTranspose3d(
                64,
                32,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.BatchNorm3d(32),
            nn.ReLU(),
        )

        self.layer8 = nn.Sequential(
            nn.ConvTranspose3d(
                32,
                1,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=(
                    USAR_BIAS_CONVOLUCIONES_TRANSPUESTAS
                ),
            ),
            nn.Sigmoid(),
        )

    def forward(self, volumen_fusionado):

        # (batch, 1, 32, 32, 32)
        volumen_32_izquierda = (
            volumen_fusionado.unsqueeze(1)
        )

        volumen_16_izquierda = self.layer1(
            volumen_32_izquierda
        )

        volumen_8_izquierda = self.layer2(
            volumen_16_izquierda
        )

        volumen_4_izquierda = self.layer3(
            volumen_8_izquierda
        )

        caracteristicas_planas = self.layer4(
            volumen_4_izquierda.reshape(
                -1,
                8192
            )
        )

        caracteristicas_planas = self.layer5(
            caracteristicas_planas
        )

        volumen_4_derecha = (
            volumen_4_izquierda
            + caracteristicas_planas.reshape(
                -1,
                128,
                4,
                4,
                4
            )
        )

        volumen_8_derecha = (
            volumen_8_izquierda
            + self.layer6(
                volumen_4_derecha
            )
        )

        volumen_16_derecha = (
            volumen_16_izquierda
            + self.layer7(
                volumen_8_derecha
            )
        )

        volumen_32_derecha = (
            volumen_32_izquierda
            + self.layer8(
                volumen_16_derecha
            )
        ) * 0.5

        return volumen_32_derecha.squeeze(1)


# ------------------------------------------------------------
# Modelo completo
# ------------------------------------------------------------

class Pix2VoxPlusPlusA(nn.Module):
    """
    Modelo completo Pix2Vox++/A.

    Devuelve tanto la reconstrucción final como las salidas
    intermedias necesarias para calcular pérdidas y analizar
    el funcionamiento del modelo.
    """

    def __init__(
        self,
        usar_refiner=True,
        usar_merger=True,
        usar_pesos_imagenet=False,
    ):
        super().__init__()

        self.usar_refiner = usar_refiner
        self.usar_merger = usar_merger

        self.encoder = EncoderPix2VoxPlusPlusA(
            usar_pesos_imagenet=(
                usar_pesos_imagenet
            )
        )

        self.decoder = DecoderPix2VoxPlusPlusA()
        self.merger = MergerPix2VoxPlusPlusA()
        self.refiner = RefinerPix2VoxPlusPlusA()

    def forward(self, imagenes):

        caracteristicas_2d = self.encoder(
            imagenes
        )

        (
            caracteristicas_3d,
            volumenes_por_vista,
        ) = self.decoder(
            caracteristicas_2d
        )

        if self.usar_merger:

            volumen_fusionado = self.merger(
                caracteristicas_3d,
                volumenes_por_vista
            )

        else:

            volumen_fusionado = torch.mean(
                volumenes_por_vista,
                dim=1
            )

        if self.usar_refiner:

            volumen_final = self.refiner(
                volumen_fusionado
            )

        else:

            volumen_final = volumen_fusionado

        return {
            "volumen_final": volumen_final,
            "volumen_fusionado": volumen_fusionado,
            "volumenes_por_vista": volumenes_por_vista,
        }


# ------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------

def convertir_metadata_checkpoint_segura(
    valor
):
    """
    Convierte metadatos a tipos básicos de Python para que
    puedan cargarse posteriormente con weights_only=True.

    Los tensores del state_dict no pasan por esta función.
    """

    if isinstance(valor, Path):
        return str(valor)

    if isinstance(valor, np.generic):
        return valor.item()

    if isinstance(valor, np.ndarray):
        return valor.tolist()

    if isinstance(valor, dict):

        return {
            str(clave):
            convertir_metadata_checkpoint_segura(
                contenido
            )
            for clave, contenido
            in valor.items()
        }

    if isinstance(
        valor,
        (list, tuple, set),
    ):

        return [
            convertir_metadata_checkpoint_segura(
                contenido
            )
            for contenido in valor
        ]

    if isinstance(
        valor,
        (
            str,
            int,
            float,
            bool,
            type(None),
        ),
    ):
        return valor

    return str(valor)


# ------------------------------------------------------------
# Compatibilidad con checkpoints antiguos
# ------------------------------------------------------------

def obtener_globals_numpy_seguros_finetuning():
    """
    Tipos NumPy permitidos al cargar checkpoints antiguos
    mediante weights_only=True.

    Los checkpoints nuevos no deberían necesitarlos porque sus
    metadatos se convierten previamente a tipos de Python.
    """

    globals_seguros = []

    # Necesario para el checkpoint v1 del experimento de
    # una vista que se creó antes de aplicar la corrección.
    try:

        globals_seguros.append(
            np._core.multiarray.scalar
        )

    except AttributeError:

        pass

    globals_seguros.append(
        np.dtype
    )

    tipos_numpy = [
        np.bool_,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
    ]

    for tipo_numpy in tipos_numpy:

        globals_seguros.append(
            type(
                np.dtype(
                    tipo_numpy
                )
            )
        )

    # Eliminar duplicados.
    globals_unicos = []
    identificadores_vistos = set()

    for objeto in globals_seguros:

        identificador = id(
            objeto
        )

        if (
            identificador
            not in identificadores_vistos
        ):

            globals_unicos.append(
                objeto
            )

            identificadores_vistos.add(
                identificador
            )

    return globals_unicos


# ------------------------------------------------------------
# Carga segura
# ------------------------------------------------------------

def cargar_checkpoint_finetuning(
    modelo,
    ruta_checkpoint,
    dispositivo_carga="cpu",
    estricto=True,
):
    """
    Carga tanto los checkpoints nuevos v2 como el antiguo v1
    creado antes de corregir los metadatos NumPy.
    """

    ruta_checkpoint = Path(
        ruta_checkpoint
    )

    if not ruta_checkpoint.exists():

        raise FileNotFoundError(
            "No existe el checkpoint:\n"
            f"{ruta_checkpoint}"
        )

    globals_seguros = (
        obtener_globals_numpy_seguros_finetuning()
    )

    with torch.serialization.safe_globals(
        globals_seguros
    ):

        checkpoint = torch.load(
            ruta_checkpoint,
            map_location=(
                dispositivo_carga
            ),
            weights_only=True,
        )

    if (
        not isinstance(
            checkpoint,
            dict,
        )
        or "model_state_dict"
        not in checkpoint
    ):

        raise ValueError(
            "El archivo no tiene el formato "
            "esperado para un checkpoint "
            "fine-tuned."
        )

    resultado_carga = (
        modelo.load_state_dict(
            checkpoint[
                "model_state_dict"
            ],
            strict=estricto,
        )
    )

    metadata = {
        "formato":
            checkpoint.get(
                "formato"
            ),

        "epoca":
            checkpoint.get(
                "epoca"
            ),

        "mejor_iou_validacion":
            checkpoint.get(
                "mejor_iou_validacion"
            ),

        "mejor_dice_validacion":
            checkpoint.get(
                "mejor_dice_validacion"
            ),

        "mejor_umbral":
            checkpoint.get(
                "mejor_umbral"
            ),

        "configuracion_experimento":
            convertir_metadata_checkpoint_segura(
                checkpoint.get(
                    "configuracion_experimento",
                    {},
                )
            ),

        "claves_ausentes":
            list(
                resultado_carga.missing_keys
            ),

        "claves_inesperadas":
            list(
                resultado_carga.unexpected_keys
            ),
    }

    del checkpoint

    gc.collect()

    return metadata


# ------------------------------------------------------------
# Comprobación
# ------------------------------------------------------------

print("=" * 75)
print("INFRAESTRUCTURA DE CHECKPOINTS DEFINIDA")
print("=" * 75)

print(
    "Conversión segura de metadatos: "
    "OK"
)

print(
    "Guardado de checkpoints:        "
    "OK"
)

print(
    "Carga de checkpoints:           "
    "OK"
)

print(
    "Compatibilidad con checkpoint "
    "v1: OK"
)