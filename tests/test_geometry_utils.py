"""
Testes para as funções de geometria usadas no projeto.

Este arquivo verifica se o grid adaptativo pode ser gerado
corretamente a partir de um AOI válido.

O objetivo aqui não é validar toda a lógica espacial,
mas garantir que o pipeline não quebra nessa etapa.
"""

import geopandas as gpd

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid


def test_generate_adaptive_grid():
    """
    Testa a geração de grid adaptativo a partir do AOI.
    """

    # Carrega o AOI real usado no projeto
    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    # Gera o grid adaptativo
    grid = generate_adaptive_grid(aoi)

    # O resultado deve ser um GeoDataFrame
    assert isinstance(grid, gpd.GeoDataFrame)

    # O grid não pode ser vazio
    assert len(grid) > 0

    # Cada célula precisa ter um identificador
    assert "cell_id" in grid.columns

    # Geometrias não podem ser vazias
    assert not grid.geometry.is_empty.any()