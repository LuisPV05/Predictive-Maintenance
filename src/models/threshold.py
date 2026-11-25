import numpy as np
import pandas as pd


def expected_cost(
    y_true, y_pred, threshold, horizon=30, cost_unplanned=5000, cost_preventive=800
):
    """Coste total de una política de alerta con un umbral dado.

    - Vehículo en alerta (pred < threshold): coste preventivo.
    - Vehículo sin alerta cuyo RUL real es <= horizon: parada no planificada.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    alert = y_pred < threshold
    missed = (~alert) & (y_true <= horizon)
    return float(alert.sum() * cost_preventive + missed.sum() * cost_unplanned)


def cost_curve(
    y_true,
    y_pred,
    thresholds=range(0, 131, 5),
    horizon=30,
    cost_unplanned=5000,
    cost_preventive=800,
):
    """Tabla con coste, alertas, fallos no detectados y falsas alarmas por umbral."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rows = []
    for t in thresholds:
        alert = y_pred < t
        fails = y_true <= horizon
        rows.append(
            {
                "umbral": t,
                "coste": expected_cost(
                    y_true, y_pred, t, horizon, cost_unplanned, cost_preventive
                ),
                "alertas": int(alert.sum()),
                "fallos_no_detectados": int(((~alert) & fails).sum()),
                "falsas_alarmas": int((alert & ~fails).sum()),
            }
        )
    return pd.DataFrame(rows)


def best_threshold(curve):
    """Fila de menor coste (si hay empate, el umbral más bajo)."""
    return curve.loc[curve["coste"].idxmin()]


def main(horizon=30, cost_unplanned=5000, cost_preventive=800):
    import matplotlib.pyplot as plt

    from src.data.load import load_cmapss, load_rul_truth
    from src.reports.fleet import load_artifacts, predict_from_raw

    model, scaler = load_artifacts()
    pred = predict_from_raw(
        load_cmapss("data/raw", split="test"), model, scaler
    )["rul_pred"]
    y_true = load_rul_truth("data/raw")["rul"]

    curve = cost_curve(
        y_true,
        pred,
        horizon=horizon,
        cost_unplanned=cost_unplanned,
        cost_preventive=cost_preventive,
    )
    best = best_threshold(curve)
    print(curve.to_string(index=False))
    print(
        f"\nUmbral óptimo: {int(best['umbral'])} ciclos "
        f"(coste {best['coste']:,.0f} €, "
        f"{int(best['fallos_no_detectados'])} fallos no detectados, "
        f"{int(best['falsas_alarmas'])} falsas alarmas)"
    )

    ax = curve.plot(x="umbral", y="coste", figsize=(7, 4), color="#1f3864", legend=False)
    ax.axvline(best["umbral"], color="#c00000", linestyle="--")
    ax.set_title(f"Coste total por umbral de alerta (fallo = RUL ≤ {horizon})")
    ax.set_xlabel("Umbral de alerta (ciclos)")
    ax.set_ylabel("Coste (€)")
    plt.tight_layout()
    plt.savefig("docs/umbral-coste.png", dpi=110)


if __name__ == "__main__":
    main()