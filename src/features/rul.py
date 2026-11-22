import pandas as pd


def add_rul(df, clip=125):
    """Añade la columna 'rul' a un DataFrame de entrenamiento.

    RUL = ciclo máximo del motor - ciclo actual, limitado a 'clip'.
    """
    df = df.copy()
    max_cycle = df.groupby("unit")["cycle"].transform("max")
    df["rul"] = max_cycle - df["cycle"]
    if clip is not None:
        df["rul"] = df["rul"].clip(upper=clip)
    return df