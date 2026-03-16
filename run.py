import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid
from src.satellite.stac_client import search_sentinel_items
from src.indices.ndvi_calculator import calculate_ndvi
from src.analysis.zonal_ndvi import compute_zonal_ndvi


def process_image(item, aoi, grid):
    """
    Processa uma única imagem Sentinel.

    Etapas:
    1) calcula NDVI
    2) executa zonal statistics no grid
    3) retorna dataframe com cell_id, date, ndvi_mean
    """
    start = time.perf_counter() #medir tempo de processamento da imagem

    # data da imagem
    date = item.properties["datetime"][:10]

    print(f"\nProcessing image: {date}")

    # calcular NDVI
    result = calculate_ndvi(item, aoi)

    if result is None:
        print("Image skipped (clouds or no intersection)")
        return None

    ndvi, transform, raster_crs = result

    print("NDVI calculated:", ndvi.shape)

    # calcular NDVI médio por célula
    zonal_result = compute_zonal_ndvi(
        ndvi,
        transform,
        grid,
        raster_crs,
    )

    # adicionar data
    zonal_result["date"] = date

    # manter apenas colunas necessárias
    zonal_result = zonal_result[
        ["cell_id", "date", "ndvi_mean"]
    ]
    end = time.perf_counter() #medir tempo de processamento da imagem
    print(f"Image {date} processed in {round(end-start,2)} seconds")

    return zonal_result


def main():

    pipeline_start = time.perf_counter() #medir tempo total do pipeline

    # --------------------------------------------------
    # 1️⃣ carregar AOI
    # --------------------------------------------------

    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    print(aoi)


    # --------------------------------------------------
    # 2️⃣ gerar grid adaptativo
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
    # 4️⃣ processar imagens em paralelo
    # --------------------------------------------------

    all_results = []

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(process_image, item, aoi, grid)
            for item in items
        ]

        for f in futures:

            result = f.result()

            if result is not None:
                all_results.append(result)


    # --------------------------------------------------
    # 5️⃣ construir dataset temporal
    # --------------------------------------------------

    if len(all_results) == 0:

        print("No valid NDVI results")
        return

    dataset = pd.concat(all_results)

    print("\nDataset preview:")
    print(dataset.head())

    print("\nTotal records:", len(dataset))


    # --------------------------------------------------
    # 6️⃣ salvar dataset
    # --------------------------------------------------

    dataset.to_csv("ndvi_timeseries.csv", index=False)

    print("\nDataset saved: ndvi_timeseries.csv")


    # --------------------------------------------------
    #  medir tempo total do pipeline
    # --------------------------------------------------    
    pipeline_end = time.perf_counter()

    print("\nPipeline runtime:", round(pipeline_end - pipeline_start, 2), "seconds")

if __name__ == "__main__":
    main()