#!/usr/bin/env python3
import os, csv, glob, subprocess
from datetime import date

def has_rows(p):
    try:
        with open(p,'r') as fh:
            dr=csv.DictReader(fh)
            for r in dr:
                if any(str(v or '').strip() for v in r.values()):
                    return True
    except Exception: pass
    return False

def first_edge(d):
    for p in (f"edge_sheet_{d}.csv","artifacts/edge_sheet_{d}.csv","edges/edge_sheet_{d}.csv"):
        if os.path.exists(p) and has_rows(p): return p
    return ""

def last_nonempty_edge():
    xs=[]
    for pat in ("edge_sheet_*.csv","artifacts/edge_sheet_*.csv","edges/edge_sheet_*.csv"):
        xs += [p for p in glob.glob(pat) if has_rows(p)]
    return sorted(xs)[-1] if xs else ""

def seed_outcomes(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_fetch_outcomes.py","--day",d,"--max","12"],check=False)

def build_edges(d):
    py=os.environ.get("PY","python3"); st=os.environ.get("STATE","TX")
    subprocess.run([py,"code_data_ingest_pricefix_v1.py","NAME=board","--date",d,"--state",st],check=False)
    subprocess.run([py,"code_cli_run_edge_sheet_v1.py","--date",d,"--cfg","config_pp_edge_v6.8.yaml"],check=False)
    return first_edge(d)

def synth_edges(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_synthesize_edges_from_outcomes.py","--day",d,"--max","12"],check=False)
    return first_edge(d)

def rejoin(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_make_training_table.py","--date",d,"--outdir","outcomes"],check=False)

D=os.environ.get("DAY") or date.today().isoformat()
edge = first_edge(D) or build_edges(D)
if not edge:
    pe=last_nonempty_edge()
    if pe:
        D=pe.split("_")[-1].split(".")[0]
        edge = first_edge(D) or build_edges(D)

seed_outcomes(D)
edge = first_edge(D) or synth_edges(D)

env=os.environ.get("GITHUB_ENV")
if env:
    with open(env,"a") as fh: fh.write(f"DAY={D}\n")

rejoin(D)
print(f"rescue_pre target={D} edge={bool(edge)}")
