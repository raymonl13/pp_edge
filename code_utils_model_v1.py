from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Union, Iterable

# Nightly writes here; keep a tolerant fallback
_MODEL_PATHS = [Path("model_assets/model_v2.pkl"), Path("model_v2.pkl")]
_CANON_FEATURES: Tuple[str, ...] = (
    "barrel_pct", "hitcher_swtr", "wrc_plus", "whiff_pct", "swing_pct",
    "hard_hit_pct", "iso", "csw_pct", "bb_k", "ld_pct", "gb_pct",
    "fb_pct", "pull_pct", "cent_pct", "oppo_pct",
)
_TARGET_CANDIDATES: Tuple[str, ...] = ("target", "y", "hit", "is_hit", "label", "outcome")

# ---- lazy model load (no exit at import) ----
_model = None
for p in _MODEL_PATHS:
    if p.exists():
        try:
            _model = joblib.load(p)
        except Exception:
            _model = None
        break

def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    num = df.select_dtypes(include=["number"]).apply(pd.to_numeric, errors="coerce").fillna(0.0)
    if num.empty:
        return num
    varying = [c for c in num.columns if num[c].nunique(dropna=False) > 1]
    return num[varying] if varying else num.iloc[:, :0]

def build_feature_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Contract for tests: RETURN (X, y_or_None)
    - Prefer canonical feature order if present; else numeric fallback without constants.
    - y is taken from a known target column if present; else None.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_feature_df expects a pandas.DataFrame")

    # separate possible target
    tcol = next((c for c in _TARGET_CANDIDATES if c in df.columns), None)
    work = df.drop(columns=[tcol], errors="ignore")

    # canonical-first feature selection
    have: Iterable[str] = [c for c in _CANON_FEATURES if c in work.columns]
    if have:
        X = work.loc[:, list(have)].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        varying = [c for c in X.columns if X[c].nunique(dropna=False) > 1]
        X = X[varying] if varying else X.iloc[:, :0]
    else:
        X = _coerce_numeric(work)

    y = None if tcol is None else df[tcol]
    return X, (y.astype(float) if y is not None else None)

def fit_model(
    X: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.Series]],
    y: Optional[Union[pd.Series, np.ndarray]] = None,
    model_path: Optional[Union[str, Path]] = None,
    *, random_state: int = 42,
):
    """Accept (X,y) or a DataFrame with a target column; optionally save model and return the Path."""
    from sklearn.linear_model import LogisticRegression
    if isinstance(X, tuple) and y is None and len(X) == 2:
        X, y = X
    if y is None:
        if isinstance(X, pd.DataFrame):
            tcol = next((c for c in _TARGET_CANDIDATES if c in X.columns), None)
            if tcol:
                y = X[tcol].to_numpy()
                X = X.drop(columns=[tcol])
            else:
                raise ValueError("fit_model expected y or a DataFrame with a target column")
        else:
            raise ValueError("fit_model expected y or a DataFrame with a target column")

    Xf = build_feature_df(X)[0] if isinstance(X, pd.DataFrame) else X
    clf = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=random_state)
    clf.fit(Xf, np.asarray(y))

    if model_path is not None:
        p = Path(model_path); p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, p)
        return p
    return clf

def predict_hit_prob(features: pd.DataFrame) -> np.ndarray:
    if _model is None:
        raise RuntimeError("model_v2 not loaded; ensure nightly downloaded artefact or skip guarded call")
    Xf, _ = build_feature_df(features)
    return _model.predict_proba(Xf)[:, 1]

__all__ = ["build_feature_df", "fit_model", "predict_hit_prob"]

