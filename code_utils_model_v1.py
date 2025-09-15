from pathlib import Path
import joblib
import numpy as np
import pandas as pd

# Canonical model locations; nightly writes to model_assets/model_v2.pkl
_MODEL_PATHS = [
    Path("model_assets/model_v2.pkl"),
    Path("model_v2.pkl"),
]

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
    return _model.predict_proba(features)[:, 1]

