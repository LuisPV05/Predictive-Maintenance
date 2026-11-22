import numpy as np
import pandas as pd


def _slope(values):
    """Pendiente de una recta ajustada a los valores (mínimos cuadrados)."""
    x = np.arange(len(values))
    if len(values) < 2:
        return 0.0
    return np.polyfit(x, values, 1)[0]


def add_rolling_slope(df, sensors, window=10):
    """Añade la pendiente móvil de cada sensor, calculada por motor."""
    df = df.copy()
    for s in sensors:
        df[f"{s}_slope{window}"] = (
            df.groupby("unit")[s]
            .rolling(window, min_periods=2)
            .apply(_slope, raw=True)
            .reset_index(level=0, drop=True)
            .fillna(0.0)
        )
    return df