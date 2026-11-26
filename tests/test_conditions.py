import numpy as np
import pandas as pd

from src.features.build import build_features, varying_sensors
from src.features.conditions import (
    assign_conditions,
    fit_condition_stats,
    fit_conditions,
    normalize_by_condition,
)


def make_df():
    rng = np.random.default_rng(0)
    n = 60
    cond = np.repeat([0, 1], n // 2)
    return pd.DataFrame(
        {
            "unit": np.repeat([1, 2], n // 2),
            "cycle": list(range(1, n // 2 + 1)) * 2,
            "setting_1": cond * 10.0 + rng.normal(scale=0.01, size=n),
            "setting_2": cond * 5.0 + rng.normal(scale=0.01, size=n),
            "setting_3": np.full(n, 100.0),
            "s2": cond * 1000.0 + rng.normal(size=n),
            "s3": rng.normal(size=n),
            "s5": np.full(n, 3.0),
        }
    )


def test_conditions_are_separated():
    df = make_df()
    conds = assign_conditions(df, fit_conditions(df, 2))
    assert conds.nunique() == 2
    assert conds.iloc[0] != conds.iloc[-1]


def test_normalization_removes_condition_offset():
    df = make_df()
    km = fit_conditions(df, 2)
    conds = assign_conditions(df, km)
    means, stds = fit_condition_stats(df, conds, ["s2"])
    out = normalize_by_condition(df, conds, ["s2"], means, stds)
    assert abs(out["s2"].mean()) < 1e-6
    assert out["s2"].abs().max() < 5  # sin el offset de 1000


def test_varying_sensors_drops_constants():
    assert varying_sensors(make_df()) == ["s2", "s3"]


def test_build_features_multi_condition():
    df = make_df()
    out, scaler = build_features(
        df, window=2, slope_window=3, clip=None, n_conditions=2
    )
    assert "s2_roll2" in out.columns and "rul" in out.columns
    # el scaler se reutiliza en test sin reajustar
    out2, _ = build_features(
        df, scaler=scaler, window=2, slope_window=3, with_rul=False, n_conditions=2
    )
    assert out2.shape[0] == df.shape[0]