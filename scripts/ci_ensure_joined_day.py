#!/usr/bin/env python3
import pandas as pd, subprocess, os, sys
df=pd.read_csv("outcomes/join_counts.csv")
if int(df["n_joined"].tail(14).sum())==0:
    day=os.environ.get("DAY","")
    if day:
        subprocess.run([os.environ.get("PY","python3"),"scripts/ci_fetch_outcomes.py","--day",day,"--max","12"],check=False)
        subprocess.run([os.environ.get("PY","python3"),"scripts/ci_make_training_table.py","--date",day,"--outdir","outcomes"],check=False)
        subprocess.run([os.environ.get("PY","python3"),"scripts/outcomes_rollup.py","--outdir","outcomes","--artifact-dir","outcomes_rollup"],check=False)
print("ok")
