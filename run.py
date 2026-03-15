"""
Arquivo principal do pipeline.

Responsável por orquestrar todo o fluxo do projeto:

1) Carregar AOI
2) Gerar grid adaptativo
3) Buscar imagens Sentinel via STAC
4) Calcular NDVI
5) Calcular NDVI médio por célula do grid
"""

# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------

# src/ingestion/aoi_loader.py
# carrega o polígono da área de interesse
from src.ingestion.aoi_loader import load_aoi

# src/utils/geometry_utils.py
# gera o grid adaptativo sobre o polígono
from src.utils.geometry_utils import generate_adaptive_grid

# src/satellite/stac_client.py
# consulta imagens Sentinel no catálogo STAC
from src.satellite.stac_client import search_sentinel_items

# src/indices/ndvi_calculator.py
# calcula NDVI a partir das bandas RED e NIR
from src.indices.ndvi_calculator import calculate_ndvi

# src/analysis/zonal_ndvi.py
# calcula NDVI médio por célula do grid
from src.analysis.zonal_ndvi import compute_zonal_ndvi


def main():

    # ---------------------------------------------------------
    # 1️⃣ CARREGAR ÁREA DE INTERESSE (AOI)
    # ---------------------------------------------------------

    # caminho do arquivo da área de interesse
    aoi_path = "data/raw/aoi_amazonia.kml"

    # carregar o polígono usando geopandas
    aoi = load_aoi(aoi_path)

    print(aoi)


    # ---------------------------------------------------------
    # 2️⃣ GERAR GRID ADAPTATIVO
    # ---------------------------------------------------------

    # subdivide o polígono em células menores
    # cada célula será usada como unidade de análise
    grid = generate_adaptive_grid(aoi)

    print(f"Grid generated with {len(grid)} cells")


    # ---------------------------------------------------------
    # 3️⃣ BUSCAR IMAGENS SENTINEL
    # ---------------------------------------------------------

    # consulta o catálogo STAC do Planetary Computer
    items = search_sentinel_items(
        aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
    )

    print("Sentinel images found:", len(items))


    # ---------------------------------------------------------
    # 4️⃣ VERIFICAR SE EXISTEM IMAGENS
    # ---------------------------------------------------------

    if len(items) == 0:

        print("No Sentinel images found")

        return


    # ---------------------------------------------------------
    # 5️⃣ PROCESSAR IMAGENS
    # ---------------------------------------------------------

    # percorremos as imagens até encontrar uma válida
    # (sem nuvem excessiva e com interseção com o AOI)

    for item in items:

        # calcular NDVI
        result = calculate_ndvi(item, aoi)

        # se a função retornar None significa:
        # - imagem não intersecta AOI
        # ou
        # - nuvem acima do limite permitido
        if result is None:

            print("Image does not intersect AOI")

            continue


        # a função retorna:
        # ndvi_array + transform espacial
        ndvi, transform, raster_crs = result

        print("NDVI calculated:", ndvi.shape)





        # ---------------------------------------------------------
        # 6️⃣ CALCULAR NDVI MÉDIO POR CÉLULA
        # ---------------------------------------------------------

        zonal_result = compute_zonal_ndvi(
            ndvi,
            transform,
            grid,
            raster_crs
        )

        # mostrar primeiras células
        print(zonal_result.head())


        # parar após primeira imagem válida
        # (isso é apenas para testes iniciais)
        break


if __name__ == "__main__":

    main()
