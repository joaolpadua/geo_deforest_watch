"""
Cálculo de NDVI médio por célula do grid.
"""

import numpy as np
from rasterio.features import geometry_mask


def compute_zonal_ndvi(ndvi, transform, grid, raster_crs):
    """
    Calcula NDVI médio para cada célula do grid.
    """

    # reprojetar grid para o CRS do raster
    grid_proj = grid.to_crs(raster_crs)

    results = []

    for _, row in grid_proj.iterrows():

        geom = [row.geometry]

        mask = geometry_mask(
            geom,
            transform=transform,
            invert=True,
            out_shape=ndvi.shape
        )

        pixels = ndvi[mask]

        if pixels.size == 0:
            mean_ndvi = np.nan
        else:
            mean_ndvi = np.nanmean(pixels)

        results.append(mean_ndvi)

    grid_result = grid_proj.copy()
    grid_result["ndvi_mean"] = results

    return grid_result
