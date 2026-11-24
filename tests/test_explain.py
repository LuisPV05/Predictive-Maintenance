import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from src.models.explain import base_sensor, contributions_by_sensor, top_drivers


def make_model():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(
        {
            "s2": rng.normal(size=80),
            "s2_roll5": rng.normal(size=80),
            "s3": rng.normal(size=80),
        }
    )
    y = 10 * X["s2"] + X["s3"] + rng.normal(scale=0.1, size=80)
    model = LGBMRegressor(n_estimators=20, min_child_samples=2, verbose=-1)
    model.fit(X, y)
    return model, X


def test_base_sensor_groups_derived_features():
    assert base_sensor("s11") == "s11"
    assert base_sensor("s11_roll5") == "s11"
    assert base_sensor("s11_slope10") == "s11"


def test_contributions_are_grouped_by_sensor():
    model, X = make_model()
    contrib = contributions_by_sensor(model, X)
    assert list(contrib.columns) == ["s2", "s3"]
    assert len(contrib) == len(X)


def test_contributions_keep_total_shap_sum():
    model, X = make_model()
    raw = model.predict(X, pred_contrib=True)
    contrib = contributions_by_sensor(model, X)
    assert np.allclose(contrib.sum(axis=1), raw[:, :-1].sum(axis=1))


def test_top_drivers_picks_most_negative():
    contrib = pd.DataFrame(
        {"s2": [-5.0, 1.0], "s3": [-1.0, 2.0], "s4": [-9.0, 0.5]}
    )
    out = top_drivers(contrib, n=2)
    assert out.iloc[0] == "s4, s2"
    assert out.iloc[1] == "-"