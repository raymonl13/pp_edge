import sys, json, datetime as dt, joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
BASE = Path(__file__).resolve().parent
MODEL = joblib.load(BASE/"model_assets"/"model_v2.pkl")["model"]
RAW = BASE/"data"/"raw"
CAL_YAML = BASE/"model_assets"/"calibration_params_v2.yaml"
def load_recent(days:int=30)->pd.DataFrame:
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    files = [f for f in RAW.glob("statcast_*") if start.strftime("%Y%m%d") <= f.stem.split("_")[1] <= end.strftime("%Y%m%d")]
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
def calibrate(df:pd.DataFrame, method:str):
    y = (df["description"]=="hit").astype(int)
    X = df.drop(columns=["description","game_date"])
    p = MODEL.predict_proba(X)[:,1]
    if method=="isotonic":
        ir = IsotonicRegression(out_of_bounds="clip").fit(p,y)
        p_cal = ir.transform(p)
        return dict(kind="isotonic", thresholds=list(ir.X_thresholds_), y_min=float(ir.y_min_), y_max=float(ir.y_max_), auc=float(roc_auc_score(y,p_cal)))
    lr = LogisticRegression(max_iter=1000).fit(p.reshape(-1,1),y)
    p_cal = lr.predict_proba(p.reshape(-1,1))[:,1]
    return dict(kind="platt", coef=float(lr.coef_[0][0]), intercept=float(lr.intercept_[0]), auc=float(roc_auc_score(y,p_cal)))
def main():
    df = load_recent()
    iso = calibrate(df,"isotonic")
    params = iso if iso["auc"] >= MODEL.booster_.best_score["training"]["auc"] - 0.03 else calibrate(df,"platt")
    with open(CAL_YAML,"w") as f:
        json.dump(params,f,indent=2)
    print(str(CAL_YAML))
if __name__=="__main__":
    sys.exit(main())
