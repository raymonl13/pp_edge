#!/usr/bin/env python3
import os, sys, glob, subprocess
import pandas as pd
from datetime import datetime

def has_rows(p):
    try:
        with open(p,'r') as f:
            for i,_ in enumerate(f,1):
                if i>1: return True
        return False
    except Exception:
        return False

def find_edge_path(day):
    for p in (f"edge_sheet_{day}.csv", f"artifacts/edge_sheet_{day}.csv", f"edges/edge_sheet_{day}.csv"):
        if os.path.exists(p) and has_rows(p):
            return p
    return ""

def latest_nonempty_edge_day():
    c=sorted(glob.glob("edge_sheet_*.csv")+glob.glob("artifacts/edge_sheet_*.csv")+glob.glob("edges/edge_sheet_*.csv"))
    for p in reversed(c):
        if has_rows(p):
            name=os.path.basename(p)
            if name.startswith("edge_sheet_"):
                return name.replace("edge_sheet_","").replace(".csv","")
    return ""

def force_build_edges(day):
    py=os.environ.get("PY","python3")
    st=os.environ.get("STATE","TX")
    subprocess.run([py,"code_data_ingest_pricefix_v1.py","--date",day,"--state",st],check=False)
    if not find_edge_path(day):
        subprocess.run([py,"scripts/ci_seed_board.py","--day",day,"--out-board",f"data/pricefix_{day}.json","--out-edges",f"edge_sheet_{day}.csv"],check=False)
    return find_edge_path(day)

def seed_outcomes(day,maxn="12"):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_fetch_outcomes.py","--day",day,"--max",maxn],check=False)

def rejoin_and_roll(day):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_make_training_table.py","--date",day,"--outdir","outcomes"],check=False)
    subprocess.run([py,"scripts/outcomes_rollup.py","--outdir","outcomes","--artifact-dir","outcomes_rollup"],check=False)

def joined_sum_last_n(n=14):
    try:
        df=pd.read_csv("outcomes/join_counts.csv")
        return int(pd.to_numeric(df.get("n_joined",pd.Series(dtype=int))).tail(n).fillna(0).sum())
    except Exception:
        return 0

day=os.environ.get("DAY","")
cov=joined_sum_last_n(14)
if cov>0:
    print(f"ensure_joined_day ok joined_sum={cov}")
    sys.exit(0)

target=day or datetime.utcnow().strftime("%Y-%m-%d")
ep=find_edge_path(target) or force_build_edges(target)
if not ep:
    alt=latest_nonempty_edge_day()
    if alt:
        target=alt
        ep=find_edge_path(target)
    if not ep:
        print(f"ensure_joined_day no_edges_for={day or 'unset'} tried_build=true still_none")
        sys.exit(0)

seed_outcomes(target,"12")
rejoin_and_roll(target)
cov2=joined_sum_last_n(14)
print(f"ensure_joined_day target={target} joined_sum_after={cov2}")
