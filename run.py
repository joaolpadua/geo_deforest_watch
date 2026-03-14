from src.ingestion.aoi_loader import load_aoi
from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid


def main():

    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    print(aoi)

    grid = generate_adaptive_grid(aoi, level="otimizado")

    grid.to_file("outputs/maps/grid.geojson", driver="GeoJSON")

    print(f"Grid generated with {len(grid)} cells")


if __name__ == "__main__":
    main()