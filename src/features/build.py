from src.features.rolling import add_rolling_mean, useful_sensors
from src.features.rul import add_rul
from src.features.scaling import apply_scaler, fit_scaler
from src.features.slopes import add_rolling_slope


def build_features(df, scaler=None, window=5, slope_window=10, clip=125, with_rul=True):
    """Construye las features finales.

    Si no se pasa scaler, se ajusta con df (modo entrenamiento).
    Devuelve (df_features, scaler).
    """
    sensors = useful_sensors(df)
    if scaler is None:
        scaler = fit_scaler(df, sensors)
    out = apply_scaler(df, sensors, scaler)
    out = add_rolling_mean(out, sensors, window)
    out = add_rolling_slope(out, sensors, slope_window)
    if with_rul:
        out = add_rul(out, clip=clip)
    return out, scaler