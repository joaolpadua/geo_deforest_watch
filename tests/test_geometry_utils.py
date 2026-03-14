"""
Testes para geração de grid adaptativo.

Esses testes verificam se:

1. O grid é gerado corretamente a partir de um AOI
2. O resultado não é vazio
3. Cada célula possui um identificador único
"""

import geopandas as gpd

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid


def test_generate_adaptive_grid():
    """
    Testa se o grid adaptativo é gerado corretamente.
    """

    # Carrega o AOI real usado no projeto
    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    # Gera o grid
    grid = generate_adaptive_grid(aoi)

    # O grid não pode ser vazio
    assert len(grid) > 0

    # Deve ser um GeoDataFrame
    assert isinstance(grid, gpd.GeoDataFrame)

    # Cada célula precisa ter um identificador
    assert "cell_id" in grid.columns