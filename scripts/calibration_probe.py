#!/usr/bin/env python3
import sys,json,pathlib,pandas as pd
day=(sys.argv[1] if len(sys.argv)>1 else "").strip()
out={"day":day or None,"join_rows":0,"brier":None,"logloss":None}
if not day:
    print(json.dumps(out)); sys.exit(0)
es=pathlib.Path(f"edge_sheet_{day}.csv")
rz=pathlib.Path(f"realized/realized_{day}.csv")
if not es.exists() or not rz.exists():
    print(json.dumps(out)); sys.exit(0)
dfp=pd.read_csv(es)
dfr=pd.read_csv(rz)
pcol="p" if "p" in dfp.columns else ("p_hit" if "p_hit" in dfp.columns else None)
if pcol is None:
    print(json.dumps(out)); sys.exit(0)
keys=None
if "leg_id" in dfp.columns and "leg_id" in dfr.columns:
    keys=["leg_id"]
elif all(c in dfp.columns for c in ["player","game_id"]) and all(c in dfr.columns for c in ["player","game_id"]):
    keys=["player","game_id"]
elif "game_id" in dfp.columns and "game_id" in dfr.columns:
    keys=["game_id"]
else:
    print(json.dumps(out)); sys.exit(0)
for k in keys:
    if k in dfr.columns: dfr[k]=dfr[k].astype(str).str.strip()
    if k in dfp.columns: dfp[k]=dfp[k].astype(str).str.strip()
left=dfr[keys+["outcome"]].copy()
right=dfp[keys+[pcol]].copy()
right=right.rename(columns={pcol:"p"})
j=left.merge(right,on=keys,how="inner",validate="m:m")
out["join_rows"]=int(len(j))
if len(j):
    import numpy as np
    p=j["p"].clip(1e-9,1-1e-9).astype(float).to_numpy()
    y=j["outcome"].astype(float).to_numpy()
    out["brier"]=float(((p-y)**2).mean())
    out["logloss"]=float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean())
print(json.dumps(out))
