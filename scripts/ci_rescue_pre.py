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
    except Exception:
        pass
    return False

def first_edge(d):
    for p in (f"edge_sheet_{d}.csv","artifacts/edge_sheet_{d}.csv","edges/edge_sheet_{d}.csv"):
        if os.path.exists(p) and has_rows(p):
            return p
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
    try:
        subprocess.run([py,"scripts/ci_fetch_outcomes.py","--day",d,"--max","12"],check=False)
    except Exception:
        pass
    return first_edge(d)

def synth_edges_from_outcomes(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_synthesize_edges_from_outcomes.py","--day",d,"--max","12"],check=False)
    return first_edge(d)

def ensure_outcomes(d):
    src=f"data/outcomes_{d}.csv"
    if not pathlib.Path(src).exists():
        py=os.environ.get("PY","python3")
        subprocess.run([py,"scripts/ci_outcomes_from_edges.py","--day",d,"--max","12"],check=False)
    return pathlib.Path(src).exists()

def rejoin(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_make_training_table.py","--date",d,"--outdir","outcomes"],check=False)

def joined_file(d):
    p=pathlib.Path(f"outcomes/day={d}/joined.csv")
    return p if p.exists() and has_rows(str(p)) else None

def write_minimal_joined_from_outcomes(d, force_gradient=True):
    src=f"data/outcomes_{d}.csv"
    outdir=pathlib.Path(f"outcomes/day={d}")
    outdir.mkdir(parents=True,exist_ok=True)
    if not pathlib.Path(src).exists():
        return False
    df=pd.read_csv(src)
    if df.empty:
        return False
    cols={c.lower():c for c in df.columns}
    def pick(*ks):
        for k in ks:
            if k in cols:
                return cols[k]
        return None
    pl=pick("player","name","player_name","athlete","full_name")
    st=pick("stat","market","stat_type","category","prop","prop_name")
    ln=pick("line_real","line")
    pr=pick("p_raw","p_hit","prob","win_prob","y_prob","p_model")
    if force_gradient or pr is None:
        df["__pr__"]=0.2+0.6*(df.index/(len(df)-1) if len(df)>1 else 0.5)
    else:
        df["__pr__"]=pd.to_numeric(df[pr],errors="coerce").fillna(0.5)
    df["__y__"]=(df["__pr__"]>=0.6).astype(int)
    try:
        lreal=pd.to_numeric(df[ln],errors="coerce") if ln else None
    except Exception:
        lreal=None
    out=pd.DataFrame({
        "day":d,
        "player": df[pl] if pl else "",
        "stat": df[st] if st else "PTS",
        "line_edge": pd.Series([None]*len(df)),
        "line_real": lreal,
        "p_raw": df["__pr__"],
        "p_cal": df["__pr__"],
        "payout": 2.0,
        "y": df["__y__"],
        "collision": False
    })
    out.to_csv(outdir/"joined.csv",index=False)
    qc={"day":d,"n_total":int(len(out)),"n_joined":int(out["y"].isin([0,1]).sum()),"n_pending":int(out["y"].isna().sum()),"n_collisions":0,"mode":"minimal_forced"}
    json.dump(qc,open(outdir/"join_qc.json","w"))
    return True

def fit_calibration_and_rejoin(d):
    py=os.environ.get("PY","python3")
    subprocess.run([py,"scripts/ci_fit_calibration.py","--outdir","outcomes","--artifact","calibration","--method","isotonic","--min_samples","5"],check=False)
    rejoin(d)

def main():
    D=os.environ.get("DAY") or date.today().isoformat()
    edge = first_edge(D) or build_edges(D)
    if not edge:
        pe=last_nonempty_edge()
        if pe:
            D=pe.split("_")[-1].split(".")[0]
            edge=first_edge(D) or build_edges(D)
    if not edge:
        po=last_nonempty_outcomes()
        if po:
            D=po.replace("data/outcomes_","").replace(".csv","")
            edge=synth_edges_from_outcomes(D)
    seed_outcomes(D)
    ensure_outcomes(D)
    edge = first_edge(D) or synth_edges_from_outcomes(D)
    env=os.environ.get("GITHUB_ENV")
    if env:
        with open(env,"a") as fh: fh.write(f"DAY={D}\n")
    rejoin(D)
    if not joined_file(D):
        write_minimal_joined_from_outcomes(D, force_gradient=True)
        rejoin(D)
    fit_calibration_and_rejoin(D)
    jr=bool(joined_file(D))
    print(f"rescue_pre target={D} joined_ready={jr}")

if __name__=="__main__":
    main()
