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

def edge_path(day):
    for p in (f"edge_sheet_{day}.csv", f"artifacts/edge_sheet_{day}.csv", f"edges/edge_sheet_{day}.csv"):
        if os.path.exists(p) and has_rows(p): return p
    return ""

def latest_nonempty_edge_day():
    c=sorted(glob.glob("edge_sheet_*.csv")+glob.glob("artifacts/edge_sheet_*.csv")+glob.glob("edges/edge_sheet_*.csv"))
    for p in reversed(c):
        if has_rows(p):
            n=os.path.basename(p)
            if n.startswith("edge_sheet_"): return n.replace("edge_sheet_","").replace(".csv","")
    return ""

def latest_nonempty_outcomes_day():
    c=sorted(glob.glob("data/outcomes_*.csv"))
    for p in reversed(c):
        if has_rows(p):
            n=os.path.basename(p)
            if n.startswith("outcomes_"): return n.replace("outcomes_","").replace(".csv","")
    return ""

def build_edges(day):
    py=os.environ.get("PY","python3")
    st=os.environ.get("STATE","TX")
    subprocess.run([py,"code_data_ingest_pricefix_v1.py","NAME=board","--date",day,"--state",st],check=False)
    subprocess.run([py,"code_cli_run_edge_sheet_v1.py","--date",day,"--cfg","config_pp_edge_v6.8.yaml"],check=False)
    if not edge_path(day):
        subprocess.run([py,"scripts/ci_seed_board.py","--day",day,"--out-board",f"data/pricefix_{day}.json","--out-edges",f"edge_sheet_{day}.csv"],check=False)
        subprocess.run([py,"code_cli_run_edge_sheet_v1.py","--date",day,"--cfg","config_pp_edge_v6.8.yaml"],check=False)
    return edge_path(day)

def synth_edges_from_outcomes(day, limit="12"):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_synthesize_edges_from_outcomes.py","--day",day,"--max",limit],check=False)
    return edge_path(day)

def seed_outcomes(day, limit="12"):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_fetch_outcomes.py","--day",day,"--max",limit],check=False)

def rejoin_and_roll(day):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_make_training_table.py","--date",day,"--outdir","outcomes"],check=False)
    subprocess.run([py,"scripts/outcomes_rollup.py","--outdir","outcomes","--artifact-dir","outcomes_rollup"],check=False)

def joined_sum(n=14):
    try:
        df=pd.read_csv("outcomes/join_counts.csv")
        return int(pd.to_numeric(df.get("n_joined",pd.Series(dtype=int))).tail(n).fillna(0).sum())
    except Exception:
        return 0

day=os.environ.get("DAY","")
if joined_sum(14)>0:
    print("ensure_joined_day ok")
    sys.exit(0)

target=day or datetime.utcnow().strftime("%Y-%m-%d")
ep=edge_path(target) or build_edges(target)
if not ep:
    alt=latest_nonempty_edge_day()
    if alt:
        target=alt
        ep=edge_path(target) or build_edges(target)

if not ep:
    alt_out=latest_nonempty_outcomes_day()
    if alt_out:
        target=alt_out
    ep=synth_edges_from_outcomes(target,"12")

if not ep:
    print(f"ensure_joined_day no_edges_for={day or 'unset'} tried_build=true tried_synth=true still_none")
    sys.exit(0)

seed_outcomes(target,"12")
if not edge_path(target) or not has_rows(edge_path(target)):
    synth_edges_from_outcomes(target,"12")

rejoin_and_roll(target)
print(f"ensure_joined_day target={target} joined_sum_after={joined_sum(14)}")
