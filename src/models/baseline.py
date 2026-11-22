import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from src.data.load import load_cmapss, load_rul_truth
from src.features.build import build_features
from src.models.metrics import mae, nasa_score, rmse

DROP_COLS = ["unit", "cycle", "rul"]


def get_xy(df):
    X = df.drop(columns=DROP_COLS)
    y = df["rul"] if "rul" in df.columns else None
    return X, y


def last_cycle_per_unit(df):
    """Última fila de cada motor (es lo que se evalúa en test)."""
    return df.sort_values(["unit", "cycle"]).groupby("unit").tail(1)


def evaluate(model, X_test, y_test, clip=125):
    pred = model.predict(X_test)
    y_true = y_test.clip(upper=clip)
    return {
        "rmse": rmse(y_true, pred),
        "mae": mae(y_true, pred),
        "nasa_score": nasa_score(y_true, pred),
    }


def main():
    train_raw = load_cmapss("data/raw", split="train")
    test_raw = load_cmapss("data/raw", split="test")
    rul_true = load_rul_truth("data/raw")

    train, scaler = build_features(train_raw)
    test, _ = build_features(test_raw, scaler=scaler, with_rul=False)

    X_train, y_train = get_xy(train)
    X_test = last_cycle_per_unit(test).drop(columns=["unit", "cycle"])
    y_test = rul_true["rul"]

    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=200, n_jobs=-1, random_state=42
        ),
    }

    rows = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        res = evaluate(model, X_test, y_test)
        rows.append({"model": name, **res})
        joblib.dump(model, f"models_{name}.joblib")

    print(pd.DataFrame(rows).round(2).to_string(index=False))
    joblib.dump(scaler, "models_scaler.joblib")


if __name__ == "__main__":
    main()