import pandas as pd


def build_ndvi_timeseries(cell_results, date):

    """
    Constrói tabela temporal de NDVI por célula.
    """

    df = cell_results.copy()

    df["date"] = date

    return df[["cell_id", "date", "ndvi_mean"]]
