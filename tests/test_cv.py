import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold

from src.models.cv import cross_validate_by_unit


def make_data():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"a": rng.normal(size=60)})
    y = pd.Series(2 * X["a"] + rng.normal(scale=0.1, size=60))
    groups = pd.Series(np.repeat(np.arange(6), 10))
    return X, y, groups


def test_groupkfold_never_splits_a_unit():
    X, y, groups = make_data()
    for tr, va in GroupKFold(n_splits=3).split(X, y, groups):
        assert set(groups.iloc[tr]).isdisjoint(set(groups.iloc[va]))


def test_cross_validate_returns_mean_and_std():
    X, y, groups = make_data()
    mean, std = cross_validate_by_unit(LinearRegression, X, y, groups, n_splits=3)
    assert mean < 1.0
    assert std >= 0.0