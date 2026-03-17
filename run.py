"""
MAIN PIPELINE
=============

Pipeline dividido em duas fases:

1️⃣ Download rasters (sequencial)
2️⃣ Processamento NDVI (paralelo)

Isso evita:

    • corrupção de arquivos
    • downloads duplicados
    • gargalo de rede
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.raster_cache import get_cached_raster
from src.indices.ndvi_calculator import calculate_ndvi
from src.grid.grid_builder import generate_grid
from src.data.sentinel_fetcher import fetch_sentinel_items
from src.utils.dataset_builder import build_dataset


def download_all_rasters(items):
    """
    Baixa todos os rasters necessários antes do processamento.

    Isso garante que o processamento paralelo não dependa de rede.
    """

    print("\nDownloading rasters...\n")

    for item in items:

        assets = item.assets

        # red band
        get_cached_raster(assets["B04"].href)

        # nir band
        get_cached_raster(assets["B08"].href)

        # scene classification
        get_cached_raster(assets["SCL"].href)


def process_image(item, aoi):
    """
    Processa uma única imagem Sentinel.

    Etapas:

        abrir rasters
        calcular NDVI
        gerar estatísticas por grid
    """

    start = time.time()

    date = item.datetime.date()

    print(f"\nProcessing image: {date}")

    result = calculate_ndvi(item, aoi)

    runtime = round(time.time() - start, 2)

    print(f"Image {date} processed in {runtime} seconds")

    return result


def main():

    pipeline_start = time.time()

    # -------------------------------------------------
    # carregar AOI
    # -------------------------------------------------

    aoi = generate_grid()

    print(f"Grid generated with {len(aoi)} cells")

    # -------------------------------------------------
    # buscar imagens Sentinel
    # -------------------------------------------------

    items = fetch_sentinel_items()

    print(f"Sentinel images found: {len(items)}")

    # -------------------------------------------------
    # STAGE 1 — DOWNLOAD
    # -------------------------------------------------

    download_all_rasters(items)

    # -------------------------------------------------
    # STAGE 2 — PROCESSAMENTO PARALELO
    # -------------------------------------------------

    results = []

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(process_image, item, aoi)
            for item in items
        ]

        for f in as_completed(futures):
            results.append(f.result())

    # -------------------------------------------------
    # construir dataset final
    # -------------------------------------------------

    dataset = build_dataset(results)

    print("\nDataset preview:\n")

    print(dataset.head())

    print(f"\nTotal records: {len(dataset)}")

    dataset.to_csv("ndvi_timeseries.csv", index=False)

    print("\nDataset saved: ndvi_timeseries.csv")

    runtime = round(time.time() - pipeline_start, 2)

    print(f"\nPipeline runtime: {runtime} seconds")


if __name__ == "__main__":
    main()