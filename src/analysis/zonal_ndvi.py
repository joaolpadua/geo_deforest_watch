import numpy as np
from rasterio.features import geometry_mask


def compute_zonal_ndvi(ndvi, transform, grid, raster_crs):

    """
    Calcula NDVI médio para cada célula do grid.

    Parâmetros
    ----------
    ndvi : numpy array
        Raster NDVI

    transform : affine
        Transform espacial do raster

    grid : GeoDataFrame
        Grid de células

    raster_crs : CRS
        Sistema de coordenadas do raster
    """

    # reprojetar grid para CRS do raster
    grid_proj = grid.to_crs(raster_crs)

    results = []

    for row in grid_proj.itertuples():

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

    grid_proj["ndvi_mean"] = results

    return grid_proj