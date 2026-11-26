from pathlib import Path

import joblib
import pandas as pd

from src.data.load import load_cmapss, load_rul_truth
from src.features.build import build_features
from src.models.baseline import last_cycle_per_unit
from src.models.explain import contributions_by_sensor, top_drivers
from src.reports.excel import SENSOR_CHART


def load_artifacts(
    model_path="models_lightgbm.joblib", scaler_path="models_scaler.joblib"
):
    return joblib.load(model_path), joblib.load(scaler_path)


def predict_from_raw(raw_df, model, scaler, with_drivers=False):
    """Predice el RUL actual de cada vehículo a partir de lecturas en bruto.

    Con with_drivers=True añade 'sensores_clave': los 3 sensores que más
    reducen el RUL de ese vehículo (SHAP).
    """
    feats, _ = build_features(raw_df, scaler=scaler, with_rul=False)
    last = last_cycle_per_unit(feats)
    X = last.drop(columns=["unit", "cycle"])
    out = pd.DataFrame(
        {
            "vehiculo": last["unit"].to_numpy(),
            "ciclos_operados": last["cycle"].to_numpy(),
            "rul_pred": model.predict(X).clip(min=0).round(1),
        }
    )
    if with_drivers:
        out["sensores_clave"] = top_drivers(
            contributions_by_sensor(model, X)
        ).to_numpy()
    return out


def predict_fleet(
    raw_path="data/raw", with_drivers=True, with_truth=True, **artifact_paths
):
    """Predice la flota de ejemplo (test_FD001).

    Con with_truth=True añade 'rul_real' si existe RUL_FD001.txt
    (mismo orden que los motores 1..100 del test).
    """
    model, scaler = load_artifacts(**artifact_paths)
    raw = load_cmapss(raw_path, split="test")
    out = predict_from_raw(raw, model, scaler, with_drivers=with_drivers)
    if with_truth and (Path(raw_path) / "RUL_FD001.txt").exists():
        out["rul_real"] = load_rul_truth(raw_path)["rul"].to_numpy()
    return out


def load_readings(raw_path="data/raw"):
    """Lecturas en bruto de la flota de ejemplo, para la hoja Sensores."""
    raw = load_cmapss(raw_path, split="test")
    cols = ["unit", "cycle"] + SENSOR_CHART
    out = raw[cols].sort_values(["unit", "cycle"]).reset_index(drop=True)
    return out.rename(columns={"unit": "vehiculo", "cycle": "ciclo"})