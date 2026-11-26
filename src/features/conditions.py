import pandas as pd
from sklearn.cluster import KMeans

SETTINGS = ["setting_1", "setting_2", "setting_3"]


def fit_conditions(df, n_conditions):
    """Agrupa las lecturas en regímenes de operación (KMeans sobre settings)."""
    km = KMeans(n_clusters=n_conditions, n_init=10, random_state=42)
    km.fit(df[SETTINGS])
    return km


def assign_conditions(df, km):
    return pd.Series(km.predict(df[SETTINGS]), index=df.index, name="cond")


def fit_condition_stats(df, conds, sensors):
    """Media y desviación de cada sensor dentro de cada condición (solo train)."""
    g = df[sensors].groupby(conds)
    return g.mean(), g.std().replace(0, 1.0).fillna(1.0)


def normalize_by_condition(df, conds, sensors, means, stds):
    out = df.copy()
    out[sensors] = (
        (df[sensors] - means.loc[conds].to_numpy()) / stds.loc[conds].to_numpy()
    )
    return out