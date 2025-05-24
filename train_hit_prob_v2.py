import sys, argparse, datetime as dt, logging, joblib, pandas as pd
from pathlib import Path
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split, GridSearchCV
BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
MODEL_DIR = BASE / "model_assets"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DEF = dict(boosting_type="dart", num_leaves=96, learning_rate=0.035, n_estimators=1100,
           feature_fraction=0.8, bagging_fraction=0.7, bagging_freq=5, lambda_l2=0.3,
           min_data_in_leaf=40, class_weight={0:1,1:2.2}, max_delta_step=0.1, n_jobs=-1)
def load_data(days:int)->pd.DataFrame:
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    files = [f for f in RAW.glob("statcast_*") if start.strftime("%Y%m%d") <= f.stem.split("_")[1] <= end.strftime("%Y%m%d")]
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
def train(df:pd.DataFrame, grid:bool):
    y = (df["description"]=="hit").astype(int)
    X = df.drop(columns=["description","game_date"])
    clf = LGBMClassifier(**DEF)
    if grid:
        gs = GridSearchCV(clf, {"num_leaves":[64,96,128], "learning_rate":[0.03,0.035,0.05]},
                          scoring="roc_auc", cv=3, n_jobs=-1)
        gs.fit(X,y)
        clf = gs.best_estimator_
    else:
        clf.fit(X,y)
    auc = roc_auc_score(y, clf.predict_proba(X)[:,1])
    logging.info("AUC %.4f", auc)
    return clf, auc
def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--grid", action="store_true")
    a = p.parse_args(argv)
    df = load_data(a.days)
    m, auc = train(df, a.grid)
    out = MODEL_DIR / "model_v2.pkl"
    joblib.dump({"model": m, "auc": auc, "trained": dt.datetime.utcnow().isoformat()}, out)
    print(out)
if __name__ == "__main__":
    sys.exit(main())
