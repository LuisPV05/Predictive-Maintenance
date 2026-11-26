from src.features.conditions import (
    assign_conditions,
    fit_condition_stats,
    fit_conditions,
    normalize_by_condition,
)
from src.features.rolling import add_rolling_mean, useful_sensors
from src.features.rul import add_rul
from src.features.scaling import apply_scaler, fit_scaler
from src.features.slopes import add_rolling_slope


def varying_sensors(df, min_std=1e-3):
    """Sensores no constantes, calculados desde los datos."""
    cols = [c for c in df.columns if c.startswith("s") and c[1:].isdigit()]
    return [c for c in cols if df[c].std() > min_std]


def build_features(
    df, scaler=None, window=5, slope_window=10, clip=125, with_rul=True,
    n_conditions=1,
):
    """Construye las features finales. Devuelve (df_features, scaler).

    n_conditions=1: MinMax global sobre sensores útiles de FD001.
    n_conditions>1: normalización por condición operativa; el 'scaler' es un
    dict con KMeans, estadísticas y sensores (se reutiliza en test).
    """
    if n_conditions == 1:
        sensors = useful_sensors(df)
        if scaler is None:
            scaler = fit_scaler(df, sensors)
        out = apply_scaler(df, sensors, scaler)
    else:
        if scaler is None:
            km = fit_conditions(df, n_conditions)
            conds = assign_conditions(df, km)
            sensors = varying_sensors(df)
            means, stds = fit_condition_stats(df, conds, sensors)
            scaler = {"km": km, "means": means, "stds": stds, "sensors": sensors}
        sensors = scaler["sensors"]
        conds = assign_conditions(df, scaler["km"])
        out = normalize_by_condition(df, conds, sensors, scaler["means"], scaler["stds"])

    out = add_rolling_mean(out, sensors, window)
    out = add_rolling_slope(out, sensors, slope_window)
    if with_rul:
        out = add_rul(out, clip=clip)
    return out, scaler