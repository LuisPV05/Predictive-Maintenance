import pandas as pd

from src.features.rolling import add_rolling_mean


def make_df():
    return pd.DataFrame(
        {
            "unit": [1, 1, 1, 2, 2, 2],
            "cycle": [1, 2, 3, 1, 2, 3],
            "s2": [10.0, 20.0, 30.0, 100.0, 200.0, 300.0],
        }
    )


def test_rolling_mean_values():
    out = add_rolling_mean(make_df(), ["s2"], window=2)
    assert out["s2_roll2"].tolist() == [10.0, 15.0, 25.0, 100.0, 150.0, 250.0]


def test_rolling_does_not_mix_units():
    out = add_rolling_mean(make_df(), ["s2"], window=3)
    # el primer valor del motor 2 no debe contener datos del motor 1
    assert out.loc[3, "s2_roll3"] == 100.0


def test_original_dataframe_not_modified():
    df = make_df()
    add_rolling_mean(df, ["s2"])
    assert "s2_roll5" not in df.columns