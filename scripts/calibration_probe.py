#!/usr/bin/env python3
import argparse, datetime as dt, json, os, pandas as pd, sys, ast, yaml
def _pick_prob(df):
    for c in ["p_hit","prob","win_prob","p"]:
        if c in df.columns: return c
    return None
def _load_labels(day):
    r1=os.path.join("realized",f"realized_{day}.csv")
    r2=os.path.join("data",f"outcomes_{day}.csv")
    for path in (r1,r2):
        if os.path.exists(path):
            df=pd.read_csv(path)
            if "y" in df.columns: return df,["leg_id","player","game_id","stat","line"]
            if "outcome" in df.columns:
                df=df.rename(columns={"outcome":"y"}); return df,["leg_id","player","game_id","stat","line"]
            if "won" in df.columns:
                df["y"]=df["won"].astype(int); return df,["leg_id","player","game_id","stat","line"]
            if "result" in df.columns:
                df["y"]=df["result"].astype(int); return df,["leg_id","player","game_id","stat","line"]
    return None
def _decode_legs_cell(s):
    if isinstance(s,(list,tuple)): return list(s)
    if not isinstance(s,str): return []
    try:
        obj=ast.literal_eval(s)
        return obj if isinstance(obj,list) else []
    except Exception:
        try:
            obj=yaml.safe_load(s)
            return obj if isinstance(obj,list) else []
        except Exception:
            return []
def _explode_legs(df):
    if "legs" not in df.columns: return df
    rows=[]
    for s in df["legs"].dropna():
        for d in _decode_legs_cell(s):
            if isinstance(d,dict): rows.append(d)
    return pd.DataFrame(rows) if rows else df
def _norm_keys(df, keys):
    out=df.copy()
    for k in keys:
        if k in out.columns:
            s=out[k].astype(str)
            s=s.replace({"nan":"","None":""})
            s=s.str.strip()
            out[k]=s
    return out
def _best_join(df, labdf, prob_col):
    cands=[["leg_id","player","game_id","stat","line"],["player","game_id","stat","line"],["player","stat","line"],["player","stat"],["player","line"],["player"]]
    for ks in cands:
        ok=[k for k in ks if k in df.columns and k in labdf.columns]
        if not ok: continue
        l=_norm_keys(df, ok)
        r=_norm_keys(labdf, ok+["y"])
        j=l.merge(r[ok+["y"]], on=ok, how="inner").dropna(subset=[prob_col,"y"])
        if len(j)>0: return j, ok
    return None, []
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day"); p.add_argument("--edges"); p.add_argument("--out")
    a=p.parse_args()
    day=a.day or dt.date.today().isoformat()
    edges=a.edges or f"edge_sheet_{day}.csv"
    out=a.out or f"calibration_{day}.json"
    payload={"day":day,"n_rows":0,"pred_col":None,"avg_pred":None,"brier":None,"n_joined":0,"join_keys":[]}
    if os.path.exists(edges):
        df=pd.read_csv(edges)
        df=_explode_legs(df)
        payload["n_rows"]=int(len(df))
        col=_pick_prob(df)
        payload["pred_col"]=col
        if col is not None and len(df):
            pcol=pd.to_numeric(df[col],errors="coerce").clip(0,1)
            payload["avg_pred"]=float(pcol.mean())
            lab=_load_labels(day)
            if lab:
                labdf,_=lab
                j,used=_best_join(df, labdf, col)
                if j is not None:
                    y=j["y"].astype(int).clip(0,1)
                    ph=pd.to_numeric(j[col],errors="coerce").clip(0,1)
                    payload["brier"]=float(((ph-y).pow(2)).mean())
                    payload["n_joined"]=int(len(j))
                    payload["join_keys"]=used
    with open(out,"w") as f: json.dump(payload,f)
    print(out)
if __name__=="__main__": sys.exit(main())
