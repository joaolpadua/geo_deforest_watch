"""
Módulo responsável por calcular NDVI a partir de imagens Sentinel-2.

Este módulo executa as seguintes etapas:

1) Verifica cobertura de nuvem dentro do AOI usando a banda SCL
2) Descarta imagens com nuvem acima do limite
3) Abre bandas RED (B04) e NIR (B08)
4) Recorta as bandas ao polígono AOI
5) Calcula NDVI
6) Retorna NDVI + transform espacial + CRS do raster
"""

import logging
import numpy as np
import rasterio
from rasterio.mask import mask
from src.utils.raster_cache import get_cached_raster

# logger para mensagens do pipeline
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CLASSES DE NUVEM DO SENTINEL SCL
# ---------------------------------------------------------
#
# A banda SCL (Scene Classification Layer) classifica cada pixel
# em diferentes tipos de cobertura.
#
# Valores relevantes:
#
# 3  → Cloud shadow
# 8  → Cloud medium probability
# 9  → Cloud high probability
# 10 → Cirrus
#
# Estes valores são considerados "nuvem".
#
CLOUD_CLASSES = {3, 8, 9, 10}


def calculate_ndvi(item, aoi, cloud_threshold=0.2):
    """
    Calcula NDVI para uma imagem Sentinel recortada ao AOI.

    Parameters
    ----------
    item : pystac.Item
        Item Sentinel retornado pelo STAC

    aoi : GeoDataFrame
        Polígono da área de interesse

    cloud_threshold : float
        Fração máxima de nuvem permitida dentro do AOI

    Returns
    -------
    tuple
        (ndvi_array, transform, raster_crs)

        ndvi_array : numpy array
            matriz NDVI

        transform : affine
            transform espacial do raster

        raster_crs : CRS
            sistema de coordenadas do raster

    ou

    None
        caso a imagem seja inválida
    """

    # ---------------------------------------------------------
    # URLs das bandas Sentinel
    # ---------------------------------------------------------

    red_url = item.assets["B04"].href
    nir_url = item.assets["B08"].href
    scl_url = item.assets["SCL"].href

    # garantir cache local
    red_path = get_cached_raster(red_url)
    nir_path = get_cached_raster(nir_url)
    scl_path = get_cached_raster(scl_url)

    try:

        # ---------------------------------------------------------
        # 1️⃣ VERIFICAR COBERTURA DE NUVEM
        # ---------------------------------------------------------

        with rasterio.open(scl_path) as scl_src:

            # reprojetar AOI para o CRS do raster
            aoi_proj = aoi.to_crs(scl_src.crs)

            # recortar raster da banda SCL ao AOI
            scl, _ = mask(scl_src, aoi_proj.geometry, crop=True)

            # remover dimensão extra (rasterio retorna [1, H, W])
            scl = scl[0]

            # total de pixels dentro do AOI
            total_pixels = scl.size

            # contar pixels classificados como nuvem
            cloud_pixels = np.isin(scl, list(CLOUD_CLASSES)).sum()

            # calcular fração de nuvem
            cloud_ratio = cloud_pixels / total_pixels

            logger.info(f"Cloud fraction inside AOI: {cloud_ratio:.2f}")

            # descartar imagem se cobertura de nuvem for alta
            if cloud_ratio > cloud_threshold:

                logger.info("Image discarded due to cloud coverage")

                return None

        # ---------------------------------------------------------
        # 2️⃣ ABRIR BANDAS RED E NIR
        # ---------------------------------------------------------

        with rasterio.open(red_path) as red_src, rasterio.open(nir_path) as nir_src:

            # reprojetar AOI para CRS das bandas
            aoi_proj = aoi.to_crs(red_src.crs)

            # recortar banda RED
            red, transform = mask(red_src, aoi_proj.geometry, crop=True)

            # recortar banda NIR
            nir, _ = mask(nir_src, aoi_proj.geometry, crop=True)

            # converter para float para evitar overflow
            red = red.astype("float32")
            nir = nir.astype("float32")

            # ---------------------------------------------------------
            # 3️⃣ CALCULAR NDVI
            # ---------------------------------------------------------
            #
            # Fórmula:
            #
            # NDVI = (NIR - RED) / (NIR + RED)
            #
            # Valores típicos:
            #
            # < 0     → água
            # 0 - 0.2 → solo exposto
            # 0.2-0.5 → vegetação baixa
            # > 0.5   → vegetação densa
            #

            ndvi = (nir - red) / (nir + red + 1e-6)

            # remover dimensão extra
            ndvi = ndvi[0]

            # obter CRS diretamente do raster
            raster_crs = red_src.crs

            # retornar NDVI + transform + CRS
            return ndvi, transform, raster_crs

    except ValueError:

        # erro ocorre quando a imagem não intersecta o AOI
        logger.warning("AOI does not intersect this Sentinel tile")

        return None
