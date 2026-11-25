import numpy as np

from src.models.threshold import best_threshold, cost_curve, expected_cost


def test_cost_counts_alerts_and_missed_failures():
    y_true = [10, 20, 100]
    y_pred = [10, 80, 100]
    # umbral 50: alerta solo al 1º (800); el 2º falla (RUL<=30) y no alerta (5000)
    assert expected_cost(y_true, y_pred, 50, horizon=30) == 800 + 5000


def test_perfect_predictions_cost_only_preventive():
    y = [5, 10, 100, 120]
    assert expected_cost(y, y, 30, horizon=30) == 2 * 800


def test_curve_has_one_row_per_threshold():
    curve = cost_curve([10, 100], [10, 100], thresholds=[0, 30, 60])
    assert len(curve) == 3
    assert list(curve["umbral"]) == [0, 30, 60]


def test_best_threshold_minimizes_cost():
    y_true = np.array([5, 10, 15, 90, 100, 120])
    y_pred = y_true.astype(float)
    best = best_threshold(cost_curve(y_true, y_pred, thresholds=range(0, 130, 5)))
    assert best["fallos_no_detectados"] == 0
    assert best["falsas_alarmas"] == 0