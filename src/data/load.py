from pathlib import Path

import pandas as pd

INDEX_COLS = ["unit", "cycle"]
SETTING_COLS = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLS = [f"s{i}" for i in range(1, 22)]
COLUMNS = INDEX_COLS + SETTING_COLS + SENSOR_COLS


def load_cmapss(path, subset="FD001", split="train"):
    """Carga un archivo C-MAPSS (train o test) con nombres de columnas."""
    file = Path(path) / f"{split}_{subset}.txt"
    if not file.exists():
        raise FileNotFoundError(f"No se encuentra {file}")
    return pd.read_csv(file, sep=r"\s+", header=None, names=COLUMNS)


def load_rul_truth(path, subset="FD001"):
    """Carga el RUL real de los motores de test."""
    file = Path(path) / f"RUL_{subset}.txt"
    if not file.exists():
        raise FileNotFoundError(f"No se encuentra {file}")
    return pd.read_csv(file, header=None, names=["rul"])