import numpy as np
from sklearn.model_selection import GroupKFold

from src.models.metrics import rmse


def cross_validate_by_unit(make_model, X, y, groups, n_splits=5):
    """CV donde todas las filas de un motor van juntas a train o a validación."""
    gkf = GroupKFold(n_splits=n_splits)
    scores = []
    for train_idx, val_idx in gkf.split(X, y, groups):
        model = make_model()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[val_idx])
        scores.append(rmse(y.iloc[val_idx], pred))
    return float(np.mean(scores)), float(np.std(scores))