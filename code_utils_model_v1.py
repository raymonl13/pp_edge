import numpy as np
from pathlib import Path
import joblib

MODEL_PATH = Path('model_assets/model_v1.pkl')

def predict_hit_prob(df, model_path: Path | None = None):
    """Return np.ndarray of p_hit for rows in *df*.
    Expects df already has final feature columns used in training.
    """
    mp = model_path or MODEL_PATH
    model = joblib.load(mp)
    return model.predict(df.fillna(0))
