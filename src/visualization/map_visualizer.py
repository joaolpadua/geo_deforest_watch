import os
import imageio
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# GERA FRAMES (MAPAS) DE NDVI AO LONGO DO TEMPO
# ---------------------------------------------------------
def generate_ndvi_frames(grid_gdf, dataset, output_dir="outputs/maps/frames"):
    """
    grid_gdf: GeoDataFrame com geometria das células
    dataset: DataFrame com colunas:
        - cell_id
        - date
        - ndvi_mean
        - alert_level (opcional)
    """

    os.makedirs(output_dir, exist_ok=True)

    # pega todas as datas únicas ordenadas
    dates = sorted(dataset["date"].unique())

    for date in dates:
        # filtra dataset para a data atual
        df_date = dataset[dataset["date"] == date]

        # junta com grid (spatial + dados)
        merged = grid_gdf.merge(df_date, on="cell_id", how="left")

        fig, ax = plt.subplots(figsize=(10, 10))

        # ---------------------------------------------------------
        # PLOT BASE: NDVI
        # ---------------------------------------------------------
        merged.plot(
            column="ndvi_mean",
            cmap="RdYlGn",
            linewidth=0,
            ax=ax,
            legend=True,
            vmin=0,
            vmax=0.8
        )

        # ---------------------------------------------------------
        # (OPCIONAL FUTURO) SOBREPOR ALERTAS
        # ---------------------------------------------------------
        if "alert_level" in merged.columns:
            alert_colors = {
                "MÉDIO": "yellow",
                "ALTO": "orange",
                "CRÍTICO": "red"
            }

            for level, color in alert_colors.items():
                subset = merged[merged["alert_level"] == level]
                if not subset.empty:
                    subset.boundary.plot(ax=ax, color=color, linewidth=1)

        # título
        num_alerts = merged["alert_level"].isin(["ALTO", "CRÍTICO"]).sum() if "alert_level" in merged.columns else 0
        ax.set_title(f"NDVI - {date} | Alerts: {num_alerts}")

        ax.axis("off")

        # salva imagem
        filepath = os.path.join(output_dir, f"ndvi_{date}.png")
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Frame salvo: {filepath}")


# ---------------------------------------------------------
# CRIA GIF A PARTIR DOS FRAMES
# ---------------------------------------------------------
def create_gif(frame_dir="outputs/maps/frames", output_path="outputs/maps/ndvi.gif"):
    """
    Lê todos os PNGs da pasta e gera um GIF animado
    """

    images = []

    files = sorted(os.listdir(frame_dir))

    for file in files:
        if file.endswith(".png"):
            filepath = os.path.join(frame_dir, file)
            images.append(imageio.imread(filepath))

    imageio.mimsave(output_path, images, duration=1)

    print(f"GIF salvo em: {output_path}")

def plot_alert_map(grid_gdf, dataset, output_path="outputs/maps/alert_map.png"):


    # pega última data (mais recente)
    latest_date = sorted(dataset["date"].unique())[-1]

    df_date = dataset[dataset["date"] == latest_date]

    merged = grid_gdf.merge(df_date, on="cell_id", how="left")

    fig, ax = plt.subplots(figsize=(10, 10))

    # base NDVI
    merged.plot(
        column="ndvi_mean",
        cmap="Greens",
        ax=ax,
        linewidth=0,
        vmin=0,
        vmax=0.8
    )

    # overlay de alertas
    alert_colors = {
        "MÉDIO": "yellow",
        "ALTO": "orange",
        "CRÍTICO": "red"
    }

    for level, color in alert_colors.items():
        subset = merged[merged["alert_level"] == level]
        if not subset.empty:
            subset.boundary.plot(ax=ax, color=color, linewidth=2)

    ax.set_title(f"Mapa de Alertas - {latest_date}")
    ax.axis("off")

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Mapa de alertas salvo em: {output_path}")