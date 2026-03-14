"""
STAC Client

Responsável por buscar imagens Sentinel-2 no Planetary Computer
usando o padrão STAC.

Fluxo:
1. conecta no catálogo STAC
2. busca imagens que intersectam o AOI
3. filtra por data
4. filtra por cobertura de nuvem
"""

import logging

import planetary_computer
from pystac_client import Client

logger = logging.getLogger(__name__)


def search_sentinel_items(
    aoi,
    start_date,
    end_date,
    max_cloud_cover=20,
):
    """
    Busca imagens Sentinel-2 que intersectam o AOI.

    Parâmetros
    ----------
    aoi : GeoDataFrame
        área de interesse

    start_date : str
        data inicial (YYYY-MM-DD)

    end_date : str
        data final

    max_cloud_cover : int
        percentual máximo de nuvem

    Retorno
    -------
    list
        lista de items STAC
    """

    logger.info("Connecting to Planetary Computer STAC")

    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1"
    )

    geometry = aoi.geometry.iloc[0].__geo_interface__

    logger.info("Searching Sentinel-2 items")

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=geometry,
        datetime=f"{start_date}/{end_date}",
        query={
            "eo:cloud_cover": {"lt": max_cloud_cover}
        },
    )

    items = list(search.items())

    logger.info("Images found: %s", len(items))

    # assinar URLs do planetary computer
    signed_items = [planetary_computer.sign(item) for item in items]

    return signed_items