import joblib
import pandas as pd
from lightgbm import LGBMRegressor

from src.data.load import load_cmapss, load_rul_truth
from src.features.build import build_features
from src.models.baseline import evaluate, get_xy, last_cycle_per_unit
from src.models.cv import cross_validate_by_unit

PARAM_GRID = [
    {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 15},
    {"n_estimators": 500, "learning_rate": 0.03, "num_leaves": 31},
    {"n_estimators": 500, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 50},
]


def make_lgbm(params):
    return LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1, **params)


def main():
    train_raw = load_cmapss("data/raw", split="train")
    test_raw = load_cmapss("data/raw", split="test")
    rul_true = load_rul_truth("data/raw")

    train, scaler = build_features(train_raw)
    test, _ = build_features(test_raw, scaler=scaler, with_rul=False)

    X_train, y_train = get_xy(train)
    groups = train["unit"]
    X_test = last_cycle_per_unit(test).drop(columns=["unit", "cycle"])
    y_test = rul_true["rul"]

    best_params, best_cv = None, float("inf")
    for params in PARAM_GRID:
        mean, std = cross_validate_by_unit(
            lambda: make_lgbm(params), X_train, y_train, groups
        )
        print(f"{params} -> CV RMSE {mean:.2f} ± {std:.2f}")
        if mean < best_cv:
            best_params, best_cv = params, mean

    model = make_lgbm(best_params)
    model.fit(X_train, y_train)
    res = evaluate(model, X_test, y_test)

    print("\nMejores parámetros:", best_params)
    print(pd.DataFrame([{"model": "lightgbm", **res}]).round(2).to_string(index=False))
    joblib.dump(model, "models_lightgbm.joblib")


if __name__ == "__main__":
    main()