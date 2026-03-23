import pandas as pd


def detect_deforestation(
    df: pd.DataFrame,
    drop_threshold: float = 0.15,
    persistence_window: int = 2,
) -> pd.DataFrame:
    """
    Detecta possíveis eventos de desmatamento com base na queda de NDVI.

    Regras:
    - queda significativa (ndvi_drop >= threshold)
    - persistência da queda nos próximos pontos

    Retorna:
    - coluna 'alert' (True/False)
    """

    df = df.copy()

    df["alert"] = False

    result = []

    for cell_id, group in df.groupby("cell_id"):

        group = group.sort_values("date").reset_index(drop=True)

        for i in range(1, len(group)):

            drop = group.loc[i, "ndvi_drop"]

            # regra 1: queda forte
            if drop >= drop_threshold:

                current_value = group.loc[i, "ndvi_mean"]

                # olhar os próximos pontos
                future_values = group.loc[
                    i : i + persistence_window, "ndvi_mean"
                ]

                # regra 2: persistência
                if len(future_values) == persistence_window + 1:

                    if all(v <= current_value for v in future_values):
                        group.loc[i, "alert"] = True

        result.append(group)

    final_df = pd.concat(result, ignore_index=True)

    return final_df