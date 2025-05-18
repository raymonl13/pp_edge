import pandas as pd, numpy as np, joblib
from pathlib import Path
from data_utils.normalize_statcast import normalize
from features import (
    rolling_woba, barrel_pct, pitcher_swstr,
    park_factor, wind_adj, travel_miles, platoon_split
)
from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV

FEATURE_ORDER = [
    "rolling_woba", "barrel_pct", "pitcher_swstr",
    "park_factor",  "wind_adj",   "travel_miles",
    "platoon_split"
]


def _feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    feats = pd.DataFrame(index=df.index)
    feats["rolling_woba"]  = rolling_woba(df)
    feats["barrel_pct"]    = barrel_pct(df)
    feats["pitcher_swstr"] = pitcher_swstr(df)
    feats["park_factor"]   = park_factor(df)
    feats["wind_adj"]      = wind_adj(df)
    feats["travel_miles"]  = travel_miles(df)
    feats["platoon_split"] = platoon_split(df)
    return feats[FEATURE_ORDER]


def build_feature_df(df: pd.DataFrame):
    X = _feature_matrix(df)
    if "is_hit" in df.columns:
        y = df["is_hit"].astype(int)
    elif "events" in df.columns:
        y = df["events"].isin({"single", "double", "triple", "home_run"}).astype(int)
    else:
        y = pd.Series(np.nan, index=df.index)
    return X, y


def fit_model(X, y, model_path: Path):
    param_grid = dict(
        n_estimators=[100, 200, 300],
        max_depth=[3, 4, 5],
        learning_rate=[0.05, 0.1, 0.2],
        subsample=[0.8, 1.0],
    )
    search = RandomizedSearchCV(
        XGBClassifier(
            tree_method="hist",
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
        ),
        param_grid,
        n_iter=15,
        cv=3,
        scoring="roc_auc",
        n_jobs=-1,
        error_score="raise",
    )
    search.fit(X, y)
    joblib.dump(search.best_estimator_, model_path)


_model_cache: dict[Path, object] = {}
def _load_model(path: Path):
    if path not in _model_cache:
        _model_cache[path] = joblib.load(path)
    return _model_cache[path]


def predict_hit_prob(
    df, model_path: Path = Path("model_assets/model_v1.pkl")
):
    # Accept dict, Series, or DataFrame
    df = df if isinstance(df, pd.DataFrame) else pd.DataFrame([df])

    # If we lack a game context, fall back to prior = 0.50
    if "game_date" not in df.columns:
        return 0.50 if len(df) == 1 else pd.Series(0.50, index=df.index)

    # Full feature path
    df = normalize(df)
    X, _ = build_feature_df(df)
    p = _load_model(model_path).predict_proba(X)[:, 1]
    return float(p[0]) if len(p) == 1 else pd.Series(p, index=df.index)
