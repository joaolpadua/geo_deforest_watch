"""
Geometry utilities

Este módulo contém funções para operações espaciais usadas no pipeline.

Responsabilidades principais:
- escolher CRS métrico adequado (UTM)
- estimar tamanho de célula do grid
- gerar grid adaptativo sobre um AOI
"""

import logging
import math

import geopandas as gpd
import numpy as np
from shapely.geometry import box

logger = logging.getLogger(__name__)


def get_utm_crs(gdf: gpd.GeoDataFrame) -> str:
    """
    Determina automaticamente um CRS UTM apropriado baseado
    no centróide da geometria.

    Trabalhar em UTM é importante porque:
    - permite medir área em metros
    - permite gerar grid com tamanho real de célula
    """

    centroid = gdf.geometry.union_all().centroid

    lon = centroid.x
    lat = centroid.y

    # calcula zona UTM a partir da longitude
    utm_zone = int((lon + 180) / 6) + 1

    # hemisfério norte ou sul
    if lat >= 0:
        return f"EPSG:{32600 + utm_zone}"

    return f"EPSG:{32700 + utm_zone}"


def estimate_cell_size(area_m2: float, level: str = "otimizado") -> float:
    """
    Estima o tamanho da célula do grid com base na área do AOI.

    Estratégia:
    Em vez de fixar tamanho de célula, definimos número alvo de células.

    Níveis:
    - otimizado → melhor performance
    - medio → mais detalhe
    - agressivo → alta resolução
    """

    targets = {
        "otimizado": 800,
        "medio": 2000,
        "agressivo": 6000,
    }

    target_cells = targets.get(level, 800)

    # área média por célula
    cell_size = math.sqrt(area_m2 / target_cells)

    # limites para evitar células absurdas
    return max(50, min(cell_size, 2000))


def generate_adaptive_grid(
    aoi: gpd.GeoDataFrame,
    level: str = "otimizado"
) -> gpd.GeoDataFrame:
    """
    Gera um grid adaptativo cobrindo o AOI.

    Fluxo:
    1. reprojeta AOI para CRS métrico
    2. calcula área
    3. estima tamanho da célula
    4. gera grid sobre bounding box
    5. mantém células que intersectam o AOI
    """

    # escolher CRS métrico
    utm_crs = get_utm_crs(aoi)
    logger.info("Selected UTM CRS: %s", utm_crs)

    # reprojetar AOI
    aoi_utm = aoi.to_crs(utm_crs)

    # calcular área
    area = aoi_utm.geometry.area.iloc[0]
    logger.info("AOI area (m²): %.2f", area)

    # estimar tamanho da célula
    cell_size = estimate_cell_size(area, level)
    logger.info("Estimated cell size (meters): %.2f", cell_size)

    # limites do AOI
    minx, miny, maxx, maxy = aoi_utm.total_bounds

    # criar coordenadas do grid
    xs = np.arange(minx, maxx, cell_size)
    ys = np.arange(miny, maxy, cell_size)

    polygons = []

    # gerar células quadradas
    for x in xs:
        for y in ys:
            polygons.append(box(x, y, x + cell_size, y + cell_size))

    grid = gpd.GeoDataFrame({"geometry": polygons}, crs=utm_crs)

    # manter apenas células que intersectam AOI
    aoi_union = aoi_utm.geometry.union_all()
    grid = grid[grid.intersects(aoi_union)].copy()

    # criar identificador único
    grid["cell_id"] = range(len(grid))

    # voltar para WGS84
    grid = grid.to_crs(4326)

    logger.info("Grid cells generated: %d", len(grid))

    return grid