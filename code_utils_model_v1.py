from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Union

# ---- Canonical model locations; nightly writes to model_assets/model_v2.pkl ----
_MODEL_PATHS = [
    Path("model_assets/model_v2.pkl"),
    Path("model_v2.pkl"),
]

# ---- Lazy-loaded model (never exit at import) ----
_model = None
for p in _MODEL_PATHS:
    if p.exists():
        try:
            _model = joblib.load(p)
        except Exception:
            _model = None
        break

def predict_hit_prob(features: pd.DataFrame) -> np.ndarray:
    """
    Return predicted hit probabilities for the provided features.
    Callers MUST ensure a model is present (or catch RuntimeError).
    """
    if _model is None:
        raise RuntimeError("model_v2 not loaded; ensure nightly downloaded artefact or skip guarded call")
    # Expect a predict_proba-compatible estimator
    return _model.predict_proba(features.fillna(0))[:, 1]

# ---- Restored public API expected by tests ----

def build_feature_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal, robust feature builder:
    - keep numeric columns only
    - coerce to numbers, fill NaN with 0
    - drop constant-variance columns (nunique <= 1)
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_feature_df expects a pandas.DataFrame")
    num = df.select_dtypes(include=["number"]).apply(pd.to_numeric, errors="coerce").fillna(0.0)
    if num.empty:
        # preserve shape/contract: return empty DF rather than raising
        return num
    varying = [c for c in num.columns if num[c].nunique(dropna=False) > 1]
    return num[varying] if varying else num.iloc[:, :0]  # empty frame if all constants

def fit_model(
    X: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.Series]],
    y: Optional[Union[pd.Series, np.ndarray]] = None,
    *,
    random_state: int = 42,
):
    """
    Minimal classifier fit that satisfies tests:
    - accepts (X, y) OR a single DataFrame with a 'target' column
    - returns an estimator exposing predict_proba(X)[:,1]
    Uses scikit-learn LogisticRegression for portability on 3.9.
    """
    from sklearn.linear_model import LogisticRegression

    # Flexible input handling
    if isinstance(X, tuple) and y is None and len(X) == 2:
        X, y = X  # type: ignore
    if y is None:
        if isinstance(X, pd.DataFrame) and "target" in X.columns:
            y = X["target"].to_numpy()
            X = X.drop(columns=["target"])
        else:
            raise ValueError("fit_model expected y or a DataFrame with a 'target' column")

    Xf = build_feature_df(X) if isinstance(X, pd.DataFrame) else X
    clf = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=random_state)
    clf.fit(Xf, np.asarray(y))
    return clf

__all__ = [
    "predict_hit_prob",
    "build_feature_df",
    "fit_model",
]

