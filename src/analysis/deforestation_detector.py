import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid
from src.satellite.stac_client import search_sentinel_items
from src.satellite.item_selection import select_best_items_per_day
from src.indices.ndvi_calculator import calculate_ndvi
from src.analysis.zonal_ndvi import compute_zonal_ndvi

from src.analysis.change_detector import compute_ndvi_change
from src.analysis.deforestation_detector import detect_deforestation


def process_image(item, aoi, grid):
    """
    Processa uma única imagem Sentinel.

    Etapas:
    1) calcula NDVI
    2) executa zonal statistics no grid
    3) retorna dataframe com cell_id, date, ndvi_mean
    """

    date = item.properties["datetime"][:10]

    print(f"\nProcessing image: {date}")

    result = calculate_ndvi(item, aoi)

    if result is None:
        print(f"Image {date} skipped (clouds or no intersection)")
        return None

    ndvi, transform, raster_crs = result

    print(f"NDVI calculated: {ndvi.shape}")

    zonal_result = compute_zonal_ndvi(
        ndvi,
        transform,
        grid,
        raster_crs,
    )

    zonal_result["date"] = date

    zonal_result = zonal_result[
        ["cell_id", "date", "ndvi_mean"]
    ]

    return zonal_result


def main():

    # --------------------------------------------------
    # 1️⃣ carregar AOI
    # --------------------------------------------------

    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    print(aoi)

    # --------------------------------------------------
    # 2️⃣ gerar grid
    # --------------------------------------------------

    grid = generate_adaptive_grid(aoi)

    print(f"Grid generated with {len(grid)} cells")

    # --------------------------------------------------
    # 3️⃣ buscar imagens Sentinel
    # --------------------------------------------------

    items = search_sentinel_items(
        aoi,
        start_date="2023-01-01",
        end_date="2023-12-31",
    )

    print("Sentinel images found:", len(items))

    if len(items) == 0:
        print("No Sentinel images found")
        return

    # --------------------------------------------------
    # 4️⃣ deduplicar STAC
    # --------------------------------------------------

    items = select_best_items_per_day(items)

    if len(items) == 0:
        print("No valid items after deduplication")
        return

    # --------------------------------------------------
    # 5️⃣ processamento paralelo
    # --------------------------------------------------

    all_results = []

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(process_image, item, aoi, grid)
            for item in items
        ]

        for f in as_completed(futures):

            result = f.result()

            if result is not None:
                all_results.append(result)

    # --------------------------------------------------
    # 6️⃣ construir dataset temporal
    # --------------------------------------------------

    if len(all_results) == 0:
        print("No valid NDVI results")
        return

    dataset = pd.concat(all_results, ignore_index=True)

    dataset = dataset.sort_values(["cell_id", "date"])

    print("\nDataset preview:")
    print(dataset.head())

    print("\nTotal records:", len(dataset))

    # --------------------------------------------------
    # 7️⃣ análise temporal (mudança NDVI)
    # --------------------------------------------------

    dataset = compute_ndvi_change(dataset)

    # --------------------------------------------------
    # 8️⃣ detecção de desmatamento
    # --------------------------------------------------

    dataset = detect_deforestation(dataset)

    print("\nAlerts preview:")
    print(dataset[dataset["alert"] == True].head())

    print("\nTotal alerts:", dataset["alert"].sum())

    # --------------------------------------------------
    # 9️⃣ salvar resultados
    # --------------------------------------------------

    dataset.to_csv("ndvi_with_alerts.csv", index=False)

    print("\nDataset saved: ndvi_with_alerts.csv")


if __name__ == "__main__":
    main()