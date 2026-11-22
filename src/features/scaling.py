from sklearn.preprocessing import MinMaxScaler


def fit_scaler(df, sensors):
    """Ajusta el scaler SOLO con datos de entrenamiento."""
    scaler = MinMaxScaler()
    scaler.fit(df[sensors])
    return scaler


def apply_scaler(df, sensors, scaler):
    """Aplica un scaler ya ajustado (sirve para train y test)."""
    df = df.copy()
    df[sensors] = scaler.transform(df[sensors])
    return df