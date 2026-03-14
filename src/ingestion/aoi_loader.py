import logging
from pathlib import Path

import geopandas as gpd

logger = logging.getLogger(__name__)


def load_aoi(file_path: str) -> gpd.GeoDataFrame:
    """
    Carrega e normaliza a Área de Interesse (AOI).

    O loader garante que:
    - o arquivo pode ser aberto
    - geometrias inválidas são corrigidas
    - múltiplos polígonos são dissolvidos
    - CRS final é EPSG:4326
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"AOI file not found: {file_path}")

    logger.info("Loading AOI from %s", file_path)

    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError("AOI file contains no geometries")

    # Corrige geometrias inválidas
    gdf["geometry"] = gdf["geometry"].buffer(0)

    gdf = gdf[gdf.geometry.notnull()]

    if gdf.empty:
        raise ValueError("No valid geometries found in AOI")

    # Dissolve múltiplas geometrias
    gdf = gdf.dissolve().reset_index(drop=True)

    if gdf.crs is None:
        raise ValueError("AOI has no CRS defined")

    # Padroniza CRS
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    logger.info("AOI loaded successfully")

    return gdf