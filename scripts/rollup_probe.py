#!/usr/bin/env python3
import os, json, glob, pathlib, pandas as pd
day=os.environ.get("DAY","").strip()
out={"day":day or None,"realized_rows":0,"prob_rows":0,"join_rows":0,"brier":None,"logloss":None}
if not day:
    paths=sorted(glob.glob("realized/realized_*.csv"))
    if not paths: print(json.dumps(out)); raise SystemExit(0)
    day=pathlib.Path(paths[-1]).stem.split("_")[-1]
    out["day"]=day
rp=f"realized/realized_{day}.csv"
if not pathlib.Path(rp).exists(): print(json.dumps(out)); raise SystemExit(0)
df_r=pd.read_csv(rp)
out["realized_rows"]=len(df_r)
es=pathlib.Path(f"edge_sheet_{day}.csv")
if not es.exists(): print(json.dumps(out)); raise SystemExit(0)
probs=pd.read_csv(es)
out["prob_rows"]=len(probs)
if "leg_id" not in df_r.columns: print(json.dumps(out)); raise SystemExit(0)
idcol="leg_id" if "leg_id" in probs.columns else ("game_id" if "game_id" in probs.columns else None)
pcol="p" if "p" in probs.columns else ("p_hit" if "p_hit" in probs.columns else None)
if not idcol or not pcol: print(json.dumps(out)); raise SystemExit(0)
df_r["leg_id"]=df_r["leg_id"].astype(str).str.strip()
probs=probs[[idcol,pcol]].copy()
probs.columns=["leg_id","p"]
probs["leg_id"]=probs["leg_id"].astype(str).str.strip()
j=pd.merge(df_r[["leg_id","outcome"]], probs, on="leg_id", how="inner")
out["join_rows"]=len(j)
if len(j):
    import numpy as np
    p=j["p"].clip(1e-9,1-1e-9).astype(float); y=j["outcome"].astype(float)
    out["brier"]=float(((p-y)**2).mean())
    out["logloss"]=float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean())
print(json.dumps(out))
