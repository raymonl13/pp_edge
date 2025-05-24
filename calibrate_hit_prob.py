import sys, json, datetime as dt, joblib, pandas as pd, numpy as np
from pathlib import Path
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "model_assets" / "model_v2.pkl"
CAL_YAML   = BASE / "model_assets" / "calibration_params_v2.yaml"

def load_model():
    return joblib.load(MODEL_PATH)["model"]

def load_recent(raw_dir: Path, days: int = 30) -> pd.DataFrame:
    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    files = [
        f for f in raw_dir.glob("statcast_*")
        if start.strftime("%Y%m%d") <= f.stem.split("_")[1] <= today.strftime("%Y%m%d")
    ]
    if not files:
        return pd.DataFrame()
    return pd.concat((pd.read_csv(f) for f in files), ignore_index=True)

def calibrate(model, df, method):
    y = (df["description"] == "hit").astype(int).to_numpy()
    X = df.drop(columns=["description", "game_date"]).to_numpy()
    p = model.predict_proba(X)[:, 1]

    if method == "isotonic":
        iso = IsotonicRegression(out_of_bounds="clip").fit(p, y)
        p_cal = iso.transform(p)
        return {
            "kind": "isotonic",
            "thresholds": list(iso.X_thresholds_),
            "y_thresholds": list(iso.y_thresholds_),
            "auc": float(roc_auc_score(y, p_cal)),
        }

    lr = LogisticRegression(max_iter=1000).fit(p.reshape(-1, 1), y)
    p_cal = lr.predict_proba(p.reshape(-1, 1))[:, 1]
    return {
        "kind": "platt",
        "coef": float(lr.coef_[0][0]),
        "intercept": float(lr.intercept_[0]),
        "auc": float(roc_auc_score(y, p_cal)),
    }

def main(argv=None):
    raw_dir = BASE / "data" / "raw"
    if argv and len(argv) == 2 and argv[0] == "--raw-dir":
        raw_dir = Path(argv[1])

    model = load_model()
    df = load_recent(raw_dir)
    if df.empty:
        print("No recent Statcast files — calibration skipped.")
        return 0

    iso = calibrate(model, df, "isotonic")
    base_auc = model.booster_.best_score["training"]["auc"]
    params = iso if iso["auc"] >= base_auc - 0.03 else calibrate(model, df, "platt")

    with open(CAL_YAML, "w") as f:
        json.dump(params, f, indent=2)
    print(CAL_YAML)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
