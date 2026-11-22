import numpy as np

from src.models.metrics import mae, nasa_score, rmse


def test_perfect_prediction():
    y = [10, 20, 30]
    assert rmse(y, y) == 0.0
    assert mae(y, y) == 0.0
    assert nasa_score(y, y) == 0.0


def test_rmse_and_mae_values():
    assert np.isclose(rmse([0, 0], [3, 4]), np.sqrt(12.5))
    assert np.isclose(mae([0, 0], [3, 4]), 3.5)


def test_nasa_score_penalizes_late_more():
    early = nasa_score([50], [40])  # predice pronto
    late = nasa_score([50], [60])   # predice tarde
    assert late > early