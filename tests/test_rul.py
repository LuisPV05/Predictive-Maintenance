import pandas as pd

from src.features.rul import add_rul


def make_df():
    return pd.DataFrame(
        {
            "unit": [1, 1, 1, 1, 2, 2, 2],
            "cycle": [1, 2, 3, 4, 1, 2, 3],
        }
    )


def test_rul_is_zero_at_last_cycle():
    out = add_rul(make_df(), clip=None)
    last = out.groupby("unit").tail(1)
    assert (last["rul"] == 0).all()


def test_rul_values_without_clip():
    out = add_rul(make_df(), clip=None)
    assert out["rul"].tolist() == [3, 2, 1, 0, 2, 1, 0]


def test_rul_clipping():
    out = add_rul(make_df(), clip=2)
    assert out["rul"].max() == 2


def test_original_dataframe_not_modified():
    df = make_df()
    add_rul(df)
    assert "rul" not in df.columns