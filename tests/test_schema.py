import pandas as pd
from data_utils.normalize_statcast import normalize

def test_schema_invariants():
    df = pd.read_csv("statcast_2024.csv", nrows=5000)
    df = normalize(df)
    assert df["game_date"].is_monotonic_increasing
    assert "park_factor" in df.columns
