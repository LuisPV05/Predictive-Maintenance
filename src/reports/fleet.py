import joblib
import pandas as pd

from src.data.load import load_cmapss
from src.features.build import build_features
from src.models.baseline import last_cycle_per_unit


def predict_fleet(
    raw_path="data/raw",
    model_path="models_lightgbm.joblib",
    scaler_path="models_scaler.joblib",
):
    """Predice el RUL actual de cada vehículo (última lectura de cada motor)."""
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    test_raw = load_cmapss(raw_path, split="test")
    test, _ = build_features(test_raw, scaler=scaler, with_rul=False)
    last = last_cycle_per_unit(test)
    X = last.drop(columns=["unit", "cycle"])

    return pd.DataFrame(
        {
            "vehiculo": last["unit"].to_numpy(),
            "ciclos_operados": last["cycle"].to_numpy(),
            "rul_pred": model.predict(X).clip(min=0).round(1),
        }
    )