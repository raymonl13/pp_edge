#!/usr/bin/env python3
from __future__ import annotations
import csv, glob, yaml
from pathlib import Path

m=Path("run_meta.txt")
lines = m.read_text().splitlines() if m.exists() else []
have = {k.split("=",1)[0] for k in lines if "=" in k}

# SLIPS_BUILT
sb = 0
p = Path("alloc_slips.csv")
if p.exists():
    with p.open() as f:
        sb = max(0, sum(1 for _ in f) - 1)

# SLIP_EV_METHOD
evm = "none"
if p.exists():
    with p.open() as f:
        r=csv.reader(f)
        next(r, None)
        row=next(r, None)
        if row and len(row)>=5: evm=row[4] or "none"

# SLIP_KEYS_OBSERVED
obs = "NONE"
edges = sorted(glob.glob("edge_sheet_*.csv"))
if edges:
    s=set()
    with open(edges[0]) as f:
        r=csv.reader(f)
        next(r, None)
        for row in r:
            if len(row)>=6 and row[5]:
                s.add(row[5])
    obs = ",".join(sorted(s)) if s else "NONE"

# SLIP_KEYS_METHOD
pref = []
cfg = Path("config_pp_edge_v6.8.yaml")
if cfg.exists():
    try:
        d=yaml.safe_load(cfg.read_text()) or {}
        pref = (d.get("slips") or {}).get("slip_types") or []
    except Exception:
        pref=[]
method="observed"
if pref and obs!="NONE":
    A=set(obs.split(",")); B=set(pref)
    if A.issubset(B): method="prefer"

out=[]
if "SLIPS_BUILT" not in have: out.append(f"SLIPS_BUILT={sb}")
if "SLIP_KEYS_METHOD" not in have: out.append(f"SLIP_KEYS_METHOD={method}")
if "SLIP_EV_METHOD" not in have: out.append(f"SLIP_EV_METHOD={evm}")
if "SLIP_KEYS_OBSERVED" not in have: out.append(f"SLIP_KEYS_OBSERVED={obs}")

if out:
    with m.open("a") as fh:
        for ln in out: fh.write(ln+"\n")
print("ENSURE_SLIP_META_DONE")
