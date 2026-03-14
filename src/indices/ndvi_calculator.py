import logging

import numpy as np
import rasterio
from rasterio.mask import mask

logger = logging.getLogger(__name__)


def calculate_ndvi(item, aoi):

    red_url = item.assets["B04"].href
    nir_url = item.assets["B08"].href

    try:

        with rasterio.open(red_url) as red_src, rasterio.open(nir_url) as nir_src:

            # reprojetar AOI para CRS do raster
            aoi_proj = aoi.to_crs(red_src.crs)

            red, _ = mask(red_src, aoi_proj.geometry, crop=True)
            nir, _ = mask(nir_src, aoi_proj.geometry, crop=True)

            red = red.astype("float32")
            nir = nir.astype("float32")

            ndvi = (nir - red) / (nir + red + 1e-6)

            return ndvi

    except ValueError:

        logger.warning("AOI does not intersect this Sentinel tile")

        return None