"""
Testes para o módulo de carregamento do AOI.

Objetivo:
Garantir que o loader consegue abrir o arquivo da área de interesse
e retornar um GeoDataFrame válido.

Não estamos testando lógica geoespacial complexa aqui.
Este teste serve apenas para garantir que o pipeline não quebra
logo na primeira etapa.
"""

import geopandas as gpd

from src.ingestion.aoi_loader import load_aoi


def test_load_aoi():
    """
    Testa se o AOI pode ser carregado corretamente.
    """

    # Caminho do AOI usado no projeto
    file_path = "data/raw/aoi_amazonia.kml"

    # Carrega o AOI
    aoi = load_aoi(file_path)

    # Verifica se retornou um GeoDataFrame
    assert isinstance(aoi, gpd.GeoDataFrame)

    # Esperamos apenas uma geometria após o dissolve
    assert len(aoi) == 1

    # Geometria não pode estar vazia
    assert not aoi.geometry.is_empty.any()

    # O CRS final deve ser WGS84 (EPSG:4326)
    assert aoi.crs.to_epsg() == 4326