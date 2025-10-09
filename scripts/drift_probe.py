#!/usr/bin/env python3
import sys, json, pathlib, pandas as pd
day = (sys.argv[1] if len(sys.argv)>1 else "").strip()
if not day:
    print(json.dumps({"error":"missing_day"})); sys.exit(0)
es = pathlib.Path(f"edge_sheet_{day}.csv")
out={"day":day,"psi":None,"ref_days":0}
if not es.exists():
    print(json.dumps(out)); sys.exit(0)
df = pd.read_csv(es)
cols = [c for c in ["p","p_hit","edge_pp","tier","slip_type"] if c in df.columns]
if not cols:
    print(json.dumps(out)); sys.exit(0)
ref = []
for p in pathlib.Path(".").glob("edge_sheet_*.csv"):
    if p.name.endswith(f"{day}.csv"):
        continue
    try:
        ref.append(pd.read_csv(p)[cols])
    except Exception:
        pass
if not ref:
    print(json.dumps(out)); sys.exit(0)
import numpy as np
refdf = pd.concat(ref, ignore_index=True)
out["ref_days"]=int(len(ref))
def psi(a,b,bins=10):
    qa = np.quantile(a, np.linspace(0,1,bins+1))
    qb = np.quantile(b, np.linspace(0,1,bins+1))
    edges = np.unique(np.concatenate([qa,qb]))
    pa,_ = np.histogram(a, bins=edges); pb,_ = np.histogram(b, bins=edges)
    pa = pa / max(pa.sum(),1); pb = pb / max(pb.sum(),1)
    s = 0.0
    for x,y in zip(pa,pb):
        x = max(x,1e-9); y = max(y,1e-9)
        s += (x - y) * np.log(x/y)
    return float(round(s,6))
scores=[]
numcol = "p" if "p" in cols else ("p_hit" if "p_hit" in cols else None)
if numcol:
    scores.append(psi(df[numcol].dropna().to_numpy(), refdf[numcol].dropna().to_numpy()))
out["psi"]=scores[0] if scores else None
print(json.dumps(out))
