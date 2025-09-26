import numpy as np, pandas as pd
from features_rolling_woba import rolling_woba

def _df(n):
    d = pd.date_range("2025-04-01", periods=n, freq="D")
    return pd.DataFrame({"game_date": d, "batter_id": 42,
                         "woba_value": 0.9, "woba_denom": 1.0})

def test_fill():
    df = _df(10)
    assert np.isclose(rolling_woba(df).iloc[-1], 0.320)

def test_mean():
    df = _df(30)
    assert np.isclose(rolling_woba(df, window_days=30).iloc[-1], 0.9)

