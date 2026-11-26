import pandas as pd
from lightgbm import LGBMRegressor

from src.data.load import load_cmapss, load_rul_truth
from src.features.build import build_features
from src.models.baseline import evaluate, get_xy, last_cycle_per_unit

# subconjunto -> número de condiciones operativas
SUBSETS = {"FD001": 1, "FD002": 6, "FD003": 1, "FD004": 6}
PARAMS = {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 15}


def run_subset(subset, n_conditions, path="data/raw"):
    train_raw = load_cmapss(path, subset=subset, split="train")
    test_raw = load_cmapss(path, subset=subset, split="test")
    rul_true = load_rul_truth(path, subset=subset)

    train, scaler = build_features(train_raw, n_conditions=n_conditions)
    test, _ = build_features(
        test_raw, scaler=scaler, with_rul=False, n_conditions=n_conditions
    )
    X_train, y_train = get_xy(train)
    X_test = last_cycle_per_unit(test).drop(columns=["unit", "cycle"])

    model = LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1, **PARAMS)
    model.fit(X_train, y_train)
    return evaluate(model, X_test, rul_true["rul"])


def main():
    rows = []
    for subset, n_cond in SUBSETS.items():
        res = run_subset(subset, n_cond)
        rows.append({"subconjunto": subset, "condiciones": n_cond, **res})
        print(rows[-1])
    print(pd.DataFrame(rows).round(2).to_string(index=False))


if __name__ == "__main__":
    main()