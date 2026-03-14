import geopandas as gpd

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid
from src.satellite.stac_client import search_sentinel_items
from src.indices.ndvi_calculator import calculate_ndvi


def main():

    # carregar AOI
    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    print(aoi)

    # gerar grid
    grid = generate_adaptive_grid(aoi)

    print(f"Grid generated with {len(grid)} cells")

    # buscar imagens Sentinel
    items = search_sentinel_items(
        aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
    )

    print("Sentinel images found:", len(items))

    # pegar primeira imagem para teste
    if len(items) == 0:
        print("No Sentinel images found")
        return

    item = items[0]

    # calcular NDVI
    ndvi = calculate_ndvi(item, aoi)

    if ndvi is not None:
        print("NDVI calculated:", ndvi.shape)
    else:
        print("Image does not intersect AOI")


if __name__ == "__main__":
    main()