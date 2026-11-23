import joblib
import pandas as pd

from src.data.load import load_cmapss
from src.features.build import build_features
from src.models.baseline import last_cycle_per_unit


def load_artifacts(
    model_path="models_lightgbm.joblib", scaler_path="models_scaler.joblib"
):
    return joblib.load(model_path), joblib.load(scaler_path)


def predict_from_raw(raw_df, model, scaler):
    """Predice el RUL actual de cada vehículo a partir de lecturas en bruto."""
    feats, _ = build_features(raw_df, scaler=scaler, with_rul=False)
    last = last_cycle_per_unit(feats)
    X = last.drop(columns=["unit", "cycle"])
    return pd.DataFrame(
        {
            "vehiculo": last["unit"].to_numpy(),
            "ciclos_operados": last["cycle"].to_numpy(),
            "rul_pred": model.predict(X).clip(min=0).round(1),
        }
    )


def predict_fleet(raw_path="data/raw", **artifact_paths):
    """Predice la flota de ejemplo (test_FD001)."""
    model, scaler = load_artifacts(**artifact_paths)
    return predict_from_raw(load_cmapss(raw_path, split="test"), model, scaler)