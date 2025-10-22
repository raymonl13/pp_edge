#!/usr/bin/env python3
import os, csv, glob, json, subprocess, pathlib
import pandas as pd
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

def last_nonempty_outcomes():
    xs=[p for p in glob.glob("data/outcomes_*.csv") if has_rows(p)]
    return sorted(xs)[-1] if xs else ""

def seed_outcomes(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_fetch_outcomes.py","--day",d,"--max","12"],check=False)

def build_edges(d):
    py=os.environ.get("PY","python3"); st=os.environ.get("STATE","TX")
    subprocess.run([py,"code_data_ingest_pricefix_v1.py","NAME=board","--date",d,"--state",st],check=False)
    subprocess.run([py,"code_cli_run_edge_sheet_v1.py","--date",d,"--cfg","config_pp_edge_v6.8.yaml"],check=False)
    return first_edge(d)

def synth_edges_from_outcomes(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_synthesize_edges_from_outcomes.py","--day",d,"--max","12"],check=False)
    return first_edge(d)

def rejoin(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_make_training_table.py","--date",d,"--outdir","outcomes"],check=False)

def joined_file(d):
    p=pathlib.Path(f"outcomes/day={d}/joined.csv")
    return p if p.exists() and has_rows(str(p)) else None

def write_minimal_joined_from_outcomes(d):
    src=f"data/outcomes_{d}.csv"
    if not os.path.exists(src) or not has_rows(src): return False
    df=pd.read_csv(src)
    cols={c.lower():c for c in df.columns}
    def pick(*ks):
        for k in ks:
            if k in cols: return cols[k]
        return None
    pl=pick("player","name","player_name","athlete","full_name")
    st=pick("stat","market","stat_type","category","prop","prop_name")
    ln=pick("line_real","line")
    pr=pick("p_raw","p_hit","prob")
    y=pick("y","won","hit","label")
    if y:
        yy=df[y]
        if yy.dtype==bool: df["y"]=yy.astype(int)
        else: df["y"]=pd.to_numeric(yy,errors="coerce")
    else:
        df["y"]=None
    out=pd.DataFrame({
        "day":d,
        "player": df[pl] if pl else "",
        "stat": df[st] if st else "PTS",
        "line_edge": pd.Series([None]*len(df)),
        "line_real": pd.to_numeric(df[ln],errors="coerce") if ln else None,
        "p_raw": pd.to_numeric(df[pr],errors="coerce") if pr else None,
        "p_cal": pd.to_numeric(df[pr],errors="coerce") if pr else None,
        "payout": 2.0,
        "y": df["y"],
        "collision": False
    })
    outdir=pathlib.Path(f"outcomes/day={d}")
    outdir.mkdir(parents=True,exist_ok=True)
    out.to_csv(outdir/"joined.csv",index=False)
    qc={"day":d,"n_total":int(len(out)),"n_joined":int(out["y"].isin([0,1]).sum()),"n_pending":int(out["y"].isna().sum()),"n_collisions":0,"mode":"minimal"}
    json.dump(qc,open(outdir/"join_qc.json","w"))
    return True

D=os.environ.get("DAY") or date.today().isoformat()
edge = first_edge(D) or build_edges(D)
if not edge:
    pe=last_nonempty_edge()
    if pe:
        D=pe.split("_")[-1].split(".")[0]
        edge = first_edge(D) or build_edges(D)
if not edge:
    po=last_nonempty_outcomes()
    if po:
        D=po.replace("data/outcomes_","").replace(".csv","")
        edge = synth_edges_from_outcomes(D)

seed_outcomes(D)
edge = first_edge(D) or synth_edges_from_outcomes(D)
if env:=os.environ.get("GITHUB_ENV"):
    open(env,"a").write(f"DAY={D}\n")

rejoin(D)
if not joined_file(D):
    write_minimal_joined_from_outcomes(D)

jf=joined_file(D)
print(f"rescue_pre target={D} edge={bool(edge)} joined_ready={bool(jf)}")
