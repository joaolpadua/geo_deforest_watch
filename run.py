import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# ingestão
from src.ingestion.aoi_loader import load_aoi
from src.utils.geometry_utils import generate_adaptive_grid

# satélite
from src.satellite.stac_client import search_sentinel_items
from src.satellite.item_selection import select_best_items_per_day

# NDVI
from src.indices.ndvi_calculator import calculate_ndvi
from src.analysis.zonal_ndvi import compute_zonal_ndvi

# análise
from src.analysis.change_detector import compute_ndvi_change
from src.analysis.deforestation_detector import detect_deforestation

# visualização
from src.visualization.map_visualizer import (
    generate_ndvi_frames,
    create_gif,
    plot_alert_map
)

# ---------------------------------------------------------
# CLASSIFICAÇÃO DE ALERTA
# ---------------------------------------------------------
def classify_alert(row):
    """
    Classifica severidade com base na queda de NDVI
    """
    if row["ndvi_drop"] >= 0.25:
        return "CRÍTICO"
    elif row["ndvi_drop"] >= 0.15:
        return "ALTO"
    elif row["ndvi_drop"] >= 0.08:
        return "MÉDIO"
    else:
        return "NORMAL"


# ---------------------------------------------------------
# FILTRO DE MEMÓRIA TEMPORAL (ANTI-RUÍDO)
# ---------------------------------------------------------
def apply_temporal_memory(df, window=3):
    """
    Mantém alertas apenas se persistirem ao longo do tempo.

    window=3 → precisa aparecer em 3 timestamps consecutivos
    """

    df = df.copy()

    def process_group(group):
        group = group.sort_values("date")

        # soma de alertas dentro da janela temporal
        group["alert_smooth"] = (
            group["alert"]
            .rolling(window=window, min_periods=1)
            .sum()
        ) >= window

        return group

    df = df.groupby("cell_id", group_keys=False).apply(process_group)

    return df


# ---------------------------------------------------------
# PROCESSAMENTO DE UMA IMAGEM
# ---------------------------------------------------------
def process_image(item, aoi, grid):
    """
    Processa 1 imagem Sentinel:
    - calcula NDVI
    - faz zonal stats por célula
    """

    date = item.properties["datetime"][:10]
    print(f"\nProcessing image: {date}")

    result = calculate_ndvi(item, aoi)

    if result is None:
        print(f"Image {date} skipped (clouds or no intersection)")
        return None

    ndvi, transform, raster_crs = result

    print(f"[{date}] NDVI calculated: {ndvi.shape}")
    print("NDVI bruto:", np.nanmin(ndvi), np.nanmax(ndvi))

    zonal_result = compute_zonal_ndvi(
        ndvi,
        transform,
        grid,
        raster_crs,
    )

    zonal_result["date"] = date

    return zonal_result[["cell_id", "date", "ndvi_mean"]]


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------
def main():

    print("\n>>> RUN COM DETECÇÃO DE DESMATAMENTO <<<\n")

    # --------------------------------------------------
    # 1️⃣ carregar AOI
    # --------------------------------------------------
    aoi = load_aoi("data/raw/aoi_amazonia.kml")
    print(aoi)

    # --------------------------------------------------
    # 2️⃣ gerar grid (divisão espacial)
    # --------------------------------------------------
    grid = generate_adaptive_grid(aoi)
    print(f"Grid generated with {len(grid)} cells")

    # --------------------------------------------------
    # 3️⃣ buscar imagens Sentinel
    # --------------------------------------------------
    items = search_sentinel_items(
        aoi,
        start_date="2020-01-01",
        end_date="2026-03-20",
    )

    print("Sentinel images found:", len(items))

    if len(items) == 0:
        print("No Sentinel images found")
        return

    # --------------------------------------------------
    # 4️⃣ deduplicar (1 imagem por dia)
    # --------------------------------------------------
    items = select_best_items_per_day(items)

    print("\nDatas finais:")
    for item in items:
        print(item.datetime.date())

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

    if len(all_results) == 0:
        print("No valid NDVI results")
        return

    # --------------------------------------------------
    # 6️⃣ dataset temporal
    # --------------------------------------------------
    dataset = pd.concat(all_results, ignore_index=True)
    dataset = dataset.sort_values(["cell_id", "date"])

    print("\nDataset preview:")
    print(dataset.head())
    print("\nTotal records:", len(dataset))

    # --------------------------------------------------
    # 7️⃣ cálculo de variação NDVI
    # --------------------------------------------------
    print("\nCalculando variação NDVI...")
    dataset = compute_ndvi_change(dataset)

    # --------------------------------------------------
    # 8️⃣ detecção de desmatamento
    # --------------------------------------------------
    print("Detectando possíveis eventos...")
    dataset = detect_deforestation(dataset)

    # --------------------------------------------------
    # 9️⃣ filtro de persistência (REMOVE RUÍDO)
    # --------------------------------------------------
    print("Aplicando persistência temporal...")

    dataset = apply_temporal_memory(dataset, window=3)

    # substitui alert pelo suavizado
    dataset["alert"] = dataset["alert_smooth"]

    # --------------------------------------------------
    # 🔟 classificação de severidade
    # --------------------------------------------------
    dataset["alert_level"] = dataset.apply(classify_alert, axis=1)

    # --------------------------------------------------
    # análise rápida
    # --------------------------------------------------
    alerts = dataset[dataset["alert"] == True]

    print("\nAlerts preview:")
    print(alerts.head())
    print("\nTotal alerts:", alerts.shape[0])

    # --------------------------------------------------
    # salvar CSV
    # --------------------------------------------------
    dataset.to_csv("ndvi_with_alerts.csv", index=False)
    print("\nDataset salvo: ndvi_with_alerts.csv")

    # --------------------------------------------------
    # gráfico exemplo (debug visual)
    # --------------------------------------------------
    import matplotlib.pyplot as plt

    cell_id = dataset["cell_id"].iloc[0]
    cell_df = dataset[dataset["cell_id"] == cell_id]

    plt.figure(figsize=(10, 5))
    plt.plot(cell_df["date"], cell_df["ndvi_mean"], marker="o")

    plt.title(f"NDVI ao longo do tempo - cell_id {cell_id}")
    plt.xlabel("Data")
    plt.ylabel("NDVI")
    plt.xticks(rotation=45)

    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # --------------------------------------------------
    # 🗺️ mapas NDVI
    # --------------------------------------------------
    print("\nGerando mapas NDVI...")
    generate_ndvi_frames(grid, dataset)

    # --------------------------------------------------
    # 🎞️ GIF temporal
    # --------------------------------------------------
    print("\nGerando GIF...")
    create_gif()

    # --------------------------------------------------
    # 🔥 mapa final com alertas
    # --------------------------------------------------
    print("\nGerando mapa de alertas...")
    plot_alert_map(grid, dataset)

    # --------------------------------------------------
    # 🌍 export GeoJSON (uso real)
    # --------------------------------------------------
    print("\nExportando GeoJSON...")

    alerts_geo = grid.merge(dataset, on="cell_id")
    alerts_geo = alerts_geo[alerts_geo["alert"] == True]

    alerts_geo.to_file("outputs/alerts.geojson", driver="GeoJSON")

    print("GeoJSON salvo em outputs/alerts.geojson")


# -------------------------------------------------------
if __name__ == "__main__":
    main()