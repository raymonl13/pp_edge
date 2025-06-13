import argparse, hashlib, joblib, pandas as pd, lightgbm as lgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
def _load(p): return pd.read_csv(p)
def _prep(df):
    y=df["is_hit"].astype(int)
    X=df.drop(columns=["is_hit"])
    return X,y
def _train(X,y):
    X_tr,X_val,y_tr,y_val=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
    model=lgb.LGBMClassifier(n_estimators=300,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,objective="binary")
    model.fit(X_tr,y_tr)
    auc=roc_auc_score(y_val,model.predict_proba(X_val)[:,1])
    return model,auc
def _sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f: h.update(f.read())
    return h.hexdigest()
def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/raw/statcast_90d.csv")
    ap.add_argument("--model-out",default="model_v2.pkl")
    ap.add_argument("--sha-out",default="model_v2.sha256")
    args=ap.parse_args(argv)
    df=_load(args.input)
    X,y=_prep(df)
    model,auc=_train(X,y)
    joblib.dump(model,args.model_out)
    digest=_sha(args.model_out)
    with open(args.sha_out,"w") as fh: fh.write(digest+"\n")
    print(f"AUC={auc:.4f} sha256={digest}")
if __name__=="__main__":
    main()
