#!/usr/bin/env python3
import argparse, datetime as dt, json, os, pandas as pd, sys, math
def parse_args():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("--day"); p.add_argument("--out")
    known, unknown = p.parse_known_args()
    day = known.day; out = known.out
    pos = [u for u in unknown if not u.startswith("-")]
    if day is None and pos: day = pos[0]
    if out is None and len(pos) > 1: out = pos[1]
    if day is None: day = dt.date.today().isoformat()
    if out is None: out = f"drift_{day}.json"
    return day, out
def psi(cur, base, bins=10):
    cur = pd.to_numeric(cur, errors="coerce").dropna()
    base = pd.to_numeric(base, errors="coerce").dropna()
    if len(cur)==0 or len(base)==0: return None
    lo, hi = float(min(cur.min(), base.min())), float(max(cur.max(), base.max()))
    if lo==hi: return 0.0
    cats = pd.cut(pd.concat([base,cur]), bins=bins, include_lowest=True, duplicates="drop").cat.categories
    b = pd.cut(base, cats, include_lowest=True).value_counts().sort_index() / len(base)
    c = pd.cut(cur,  cats, include_lowest=True).value_counts().sort_index() / len(cur)
    eps=1e-8
    return float(((c-b)*((c+eps)/(b+eps)).apply(lambda x: 0.0 if x<=0 else math.log(x))).sum())
def main():
    day, out = parse_args()
    prev = (dt.date.fromisoformat(day)-dt.timedelta(days=1)).isoformat()
    curp  = f"edge_sheet_{day}.csv"
    basep = f"edge_sheet_{prev}.csv"
    feat=None; v=None; ncur=0; nref=None; ref_days=0
    if os.path.exists(curp):
        cur = pd.read_csv(curp); ncur = int(len(cur))
        for c in ["edge_pp","p_hit","prob","p"]:
            if c in cur.columns: feat=c; break
        if feat and os.path.exists(basep):
            base = pd.read_csv(basep); nref = int(len(base)); ref_days=1
            v = psi(cur[feat], base[feat])
    payload = {"day": day, "psi": v, "rows_current": ncur, "rows_ref": nref, "ref_days": ref_days}
    with open(out,"w") as f: json.dump(payload,f)
    print(out)
if __name__=="__main__": sys.exit(main())
