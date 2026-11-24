import re

import pandas as pd

SUFFIX = re.compile(r"_(roll|slope)\d+$")


def base_sensor(feature):
    """'s11_roll5' y 's11_slope10' se agrupan en 's11'."""
    return SUFFIX.sub("", feature)


def contributions_by_sensor(model, X):
    """Contribución SHAP de cada sensor a cada predicción de RUL.

    Valores negativos = el sensor empuja el RUL hacia abajo (degradación).
    """
    contrib = model.predict(X, pred_contrib=True)  # última columna = base
    feats = pd.DataFrame(contrib[:, :-1], columns=X.columns, index=X.index)
    return feats.T.groupby(base_sensor).sum().T


def top_drivers(contrib, n=3):
    """Texto con los n sensores que más reducen el RUL de cada fila."""

    def pick(row):
        worst = row[row < 0].nsmallest(n)
        return ", ".join(worst.index) if len(worst) else "-"

    return contrib.apply(pick, axis=1)


def main():
    import matplotlib.pyplot as plt

    import joblib

    from src.data.load import load_cmapss
    from src.features.build import build_features
    from src.models.baseline import get_xy

    model = joblib.load("models_lightgbm.joblib")
    train, _ = build_features(load_cmapss("data/raw", split="train"))
    X, _ = get_xy(train)
    contrib = contributions_by_sensor(model, X)
    importance = contrib.abs().mean().sort_values().tail(12)

    ax = importance.plot.barh(figsize=(7, 5), color="#1f3864")
    ax.set_title("Importancia de sensores (media |SHAP|, ciclos de RUL)")
    ax.set_xlabel("Impacto medio en el RUL predicho")
    plt.tight_layout()
    plt.savefig("docs/importancia-sensores.png", dpi=110)
    print(importance.round(2).sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()