import numpy as np
import pandas as pd

from src.features.build import build_features
from src.features.scaling import apply_scaler, fit_scaler
from src.features.slopes import add_rolling_slope


def make_df():
    return pd.DataFrame(
        {
            "unit": [1] * 5 + [2] * 5,
            "cycle": list(range(1, 6)) * 2,
            "s2": [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            "s3": [5.0, 4.0, 3.0, 2.0, 1.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )


def test_slope_of_linear_signal():
    out = add_rolling_slope(make_df(), ["s2"], window=3)
    assert np.isclose(out.loc[4, "s2_slope3"], 1.0)
    assert np.isclose(out.loc[9, "s2_slope3"], 0.0)


def test_slope_does_not_mix_units():
    out = add_rolling_slope(make_df(), ["s2"], window=3)
    assert out.loc[5, "s2_slope3"] == 0.0


def test_scaler_range():
    df = make_df()
    scaler = fit_scaler(df, ["s2", "s3"])
    out = apply_scaler(df, ["s2", "s3"], scaler)
    assert out[["s2", "s3"]].min().min() == 0.0
    assert out[["s2", "s3"]].max().max() == 1.0


def test_scaler_fit_only_on_train():
    train = make_df()
    scaler = fit_scaler(train, ["s2"])
    test = train.copy()
    test["s2"] = 20.0
    out = apply_scaler(test, ["s2"], scaler)
    assert out["s2"].iloc[0] > 1.0  # el test no cambia el scaler


def test_build_features_adds_columns_and_rul():
    df = make_df()
    out, scaler = build_features(df, window=2, slope_window=3, clip=None)
    assert "rul" in out.columns
    assert "s2_roll2" in out.columns
    assert "s2_slope3" in out.columns