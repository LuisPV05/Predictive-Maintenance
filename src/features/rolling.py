import pandas as pd

# Sensores constantes o casi constantes en FD001 (no aportan información)
DROP_SENSORS = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]


def useful_sensors(df):
    """Devuelve la lista de sensores que no son constantes en FD001."""
    return [c for c in df.columns if c.startswith("s") and c[1:].isdigit() and c not in DROP_SENSORS]


def add_rolling_mean(df, sensors, window=5):
    """Añade la media móvil de cada sensor, calculada por motor."""
    df = df.copy()
    for s in sensors:
        df[f"{s}_roll{window}"] = (
            df.groupby("unit")[s]
            .rolling(window, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )
    return df