import pandas as pd
from data_utils.normalize_statcast import normalize
from code_utils_model_v1 import build_feature_df

def test_feature_variance():
    df = normalize(pd.read_csv("statcast_2024.csv").head(10000))
    X, _ = build_feature_df(df)
    flat = [c for c in X.columns if X[c].std() == 0]
    assert not flat, f"Flat features detected: {flat}"
