import pandas as pd


def compute_ndvi_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a variação temporal de NDVI por célula.

    Retorna:
    - ndvi_prev
    - ndvi_drop
    """

    df = df.copy()

    df = df.sort_values(["cell_id", "date"])

    result = []

    for cell_id, group in df.groupby("cell_id"):

        group = group.sort_values("date").reset_index(drop=True)

        group["ndvi_prev"] = group["ndvi_mean"].shift(1)
        group["ndvi_drop"] = group["ndvi_prev"] - group["ndvi_mean"]

        result.append(group)

    final_df = pd.concat(result, ignore_index=True)

    return final_df