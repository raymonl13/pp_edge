import sys, json, datetime as dt, joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
BASE = Path(__file__).resolve().parent
RAW = BASE/"data"/"raw"
MODEL_PATH = BASE/"model_assets"/"model_v2.pkl"
CAL_YAML = BASE/"model_assets"/"calibration_params_v2.yaml"
def load_model():
    return joblib.load(MODEL_PATH)["model"]
def load_recent(days:int=30):
    end = dt.date.today(); start = end - dt.timedelta(days=days)
    files = [f for f in RAW.glob("statcast_*") if start.strftime("%Y%m%d") <= f.stem.split("_")[1] <= end.strftime("%Y%m%d")]
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
def calibrate(model,df,method):
    y = (df["description"]=="hit").astype(int)
    X = df.drop(columns=["description","game_date"])
    p = model.predict_proba(X)[:,1]
    if method=="isotonic":
        iso = IsotonicRegression(out_of_bounds="clip").fit(p,y)
        p_cal = iso.transform(p)
        return dict(kind="isotonic", thresholds=list(iso.X_thresholds_), y_min=float(iso.y_min_), y_max=float(iso.y_max_), auc=float(roc_auc_score(y,p_cal)))
    lr = LogisticRegression(max_iter=1000).fit(p.reshape(-1,1),y)
    p_cal = lr.predict_proba(p.reshape(-1,1))[:,1]
    return dict(kind="platt", coef=float(lr.coef_[0][0]), intercept=float(lr.intercept_[0]), auc=float(roc_auc_score(y,p_cal)))
def main():
    model = load_model()
    df = load_recent()
    iso = calibrate(model,df,"isotonic")
    base_auc = model.booster_.best_score["training"]["auc"]
    params = iso if iso["auc"] >= base_auc - 0.03 else calibrate(model,df,"platt")
    with open(CAL_YAML,"w") as f:
        json.dump(params,f,indent=2)
    print(CAL_YAML)
if __name__=="__main__":
    sys.exit(main())
