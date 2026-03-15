import pandas as pd

from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid
from src.satellite.stac_client import search_sentinel_items
from src.indices.ndvi_calculator import calculate_ndvi
from src.analysis.zonal_ndvi import compute_zonal_ndvi


def main():

    # --------------------------------------------------
    # 1️⃣ Carregar AOI (Área de Interesse)
    # --------------------------------------------------
    # Arquivo KML contendo o polígono da área que queremos analisar

    aoi = load_aoi("data/raw/aoi_amazonia.kml")

    print(aoi)


    # --------------------------------------------------
    # 2️⃣ Gerar grid espacial adaptativo
    # --------------------------------------------------
    # O polígono é dividido em várias células menores.
    # Cada célula será analisada individualmente.

    grid = generate_adaptive_grid(aoi)

    print(f"Grid generated with {len(grid)} cells")


    # --------------------------------------------------
    # 3️⃣ Buscar imagens Sentinel no STAC
    # --------------------------------------------------
    # Planetary Computer retorna todas as imagens Sentinel
    # que intersectam a área dentro do intervalo de datas.

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
    # 4️⃣ Lista para armazenar resultados temporais
    # --------------------------------------------------
    # Cada imagem vai gerar NDVI por célula.
    # Depois juntaremos tudo em um dataset.

    all_results = []


    # --------------------------------------------------
    # 5️⃣ Loop nas imagens Sentinel
    # --------------------------------------------------

    for item in items:

        # data da imagem
        date = item.properties["datetime"][:10]

        print(f"\nProcessing image: {date}")

        # --------------------------------------------------
        # calcular NDVI
        # --------------------------------------------------

        result = calculate_ndvi(item, aoi)

        # imagem pode ser descartada por:
        # - nuvem
        # - não intersectar AOI
        if result is None:

            print("Image skipped (clouds or no intersection)")
            continue

        ndvi, transform, raster_crs = result

        print("NDVI calculated:", ndvi.shape)


        # --------------------------------------------------
        # calcular NDVI médio por célula (zonal statistics)
        # --------------------------------------------------

        zonal_result = compute_zonal_ndvi(
            ndvi,
            transform,
            grid,
            raster_crs,
        )


        # --------------------------------------------------
        # adicionar data
        # --------------------------------------------------

        zonal_result["date"] = date


        # --------------------------------------------------
        # manter apenas colunas necessárias
        # --------------------------------------------------

        zonal_result = zonal_result[
            ["cell_id", "date", "ndvi_mean"]
        ]


        # armazenar resultado
        all_results.append(zonal_result)


    # --------------------------------------------------
    # 6️⃣ Construir dataset temporal completo
    # --------------------------------------------------

    if len(all_results) == 0:

        print("No valid NDVI results")
        return

    dataset = pd.concat(all_results)

    print("\nDataset preview:")
    print(dataset.head())

    print("\nTotal records:", len(dataset))


    # --------------------------------------------------
    # 7️⃣ Salvar dataset
    # --------------------------------------------------

    dataset.to_csv("ndvi_timeseries.csv", index=False)

    print("\nDataset saved: ndvi_timeseries.csv")


if __name__ == "__main__":
    main()

