#!/usr/bin/env python3
import sys, json, pathlib, pandas as pd
day = (sys.argv[1] if len(sys.argv)>1 else "").strip()
if not day:
    print(json.dumps({"error":"missing_day"})); sys.exit(0)
es = pathlib.Path(f"edge_sheet_{day}.csv")
rz = pathlib.Path(f"realized/realized_{day}.csv")
out = {"day":day,"join_rows":0,"brier":None,"logloss":None}
if not es.exists() or not rz.exists():
    print(json.dumps(out)); sys.exit(0)
dfp = pd.read_csv(es)
dfr = pd.read_csv(rz)
idcol = "leg_id" if "leg_id" in dfp.columns and "leg_id" in dfr.columns else None
pcol  = "p" if "p" in dfp.columns else ("p_hit" if "p_hit" in dfp.columns else None)
if not idcol or not pcol:
    print(json.dumps(out)); sys.exit(0)
dfr[idcol] = dfr[idcol].astype(str).str.strip()
dfp[idcol] = dfp[idcol].astype(str).str.strip()
j = dfr[[idcol,"outcome"]].merge(dfp[[idcol,pcol]].rename(columns={pcol:"p"}), on=idcol, how="inner")
out["join_rows"] = int(len(j))
if len(j):
    import numpy as np
    p = j["p"].clip(1e-9,1-1e-9).astype(float).to_numpy()
    y = j["outcome"].astype(float).to_numpy()
    out["brier"]  = float(((p-y)**2).mean())
    out["logloss"]= float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean())
print(json.dumps(out))
