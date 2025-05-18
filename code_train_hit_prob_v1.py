from pathlib import Path
from typing import Optional
import pandas as pd
from data_utils.normalize_statcast import normalize
from code_utils_model_v1 import build_feature_df, fit_model
from code_data_ingest_statcast import ingest_statcast

def train(model_path: Path,
          df: Optional[pd.DataFrame] = None,
          rows: Optional[int] = None):
    if df is None:
        raw = ingest_statcast("statcast_2024.csv", "statcast_2025.csv", "park_factors.csv")
        if rows:
            raw = raw.head(rows)
        df = normalize(raw)
    X, y = build_feature_df(df)
    fit_model(X, y, model_path)

if __name__ == "__main__":
    train(Path("model_assets/model_v1.pkl"))
