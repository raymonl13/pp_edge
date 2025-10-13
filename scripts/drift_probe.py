import sys,os,math,json
from datetime import datetime,timedelta
try:
    import pandas as pd
except Exception:
    print(json.dumps({"day":sys.argv[1] if len(sys.argv)>1 else "", "psi":None, "rows_current":None, "rows_ref":None, "ref_days":0})); sys.exit(0)
def psi(cur, ref, bins=10, eps=1e-6):
    qs=[i/bins for i in range(bins+1)]
    edges=ref.quantile(qs).values
    edges[0]=min(edges[0],cur.min(),ref.min())-eps
    edges[-1]=max(edges[-1],cur.max(),ref.max())+eps
    c=pd.cut(cur, edges, include_lowest=True).value_counts().sort_index()
    r=pd.cut(ref, edges, include_lowest=True).value_counts().sort_index()
    c=(c/c.sum()).clip(eps,1).values
    r=(r/r.sum()).clip(eps,1).values
    return float(((c-r)*np.log(c/r)).sum())
import numpy as np
import pandas as pd
day = sys.argv[1] if len(sys.argv)>1 else ""
if not day:
    print(json.dumps({"day":"","psi":None,"rows_current":None,"rows_ref":None,"ref_days":0})); sys.exit(0)
cur_path=f"edge_sheet_{day}.csv"
try:
    cur=pd.read_csv(cur_path)
except Exception:
    print(json.dumps({"day":day,"psi":None,"rows_current":0,"rows_ref":None,"ref_days":0})); sys.exit(0)
try:
    d=datetime.strptime(day,"%Y-%m-%d")
    y=(d-timedelta(days=1)).strftime("%Y-%m-%d")
except Exception:
    y=""
ref_path=f"edge_sheet_{y}.csv" if y else ""
ref=None
ref_days=0
if ref_path and os.path.exists(ref_path):
    try:
        ref=pd.read_csv(ref_path); ref_days=1
    except Exception:
        ref=None; ref_days=0
rows_cur=int(cur.shape[0])
rows_ref=int(ref.shape[0]) if isinstance(ref,pd.DataFrame) else None
pcol=None
for c in ["p_hit","p"]:
    if c in cur.columns: pcol=c; break
if pcol is None:
    print(json.dumps({"day":day,"psi":None,"rows_current":rows_cur,"rows_ref":rows_ref,"ref_days":ref_days})); sys.exit(0)
if not isinstance(ref,pd.DataFrame) or pcol not in ref.columns or rows_cur<10 or (rows_ref or 0)<10:
    print(json.dumps({"day":day,"psi":None,"rows_current":rows_cur,"rows_ref":rows_ref,"ref_days":ref_days})); sys.exit(0)
try:
    v=float(psi(cur[pcol].astype(float), ref[pcol].astype(float), bins=10))
except Exception:
    v=None
print(json.dumps({"day":day,"psi":v,"rows_current":rows_cur,"rows_ref":rows_ref,"ref_days":ref_days}))
