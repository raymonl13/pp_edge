#!/usr/bin/env python3
import argparse, os, sys, glob, math
import pandas as pd
import numpy as np
def list_joined(outdir): return sorted(glob.glob(f"{outdir}/day=*/joined.csv"))
def safe_brier(p,y):
    m=p.notna() & y.notna()
    if not m.any(): return float("nan")
    return float(((p[m]-y[m])**2).mean())
def safe_logloss(p,y,eps=1e-12):
    m=p.notna() & y.notna()
    if not m.any(): return float("nan")
    p=p[m].clip(eps,1-eps); y=y[m]
    return float((-(y*np.log(p)+(1-y)*np.log(1-p))).mean())
def summarize_day(path):
    d=path.split("day=")[1].split("/")[0]
    try: df=pd.read_csv(path)
    except Exception: return {"day":d,"n_total":0,"n_joined":0,"n_pending":0,"roi_units":float("nan"),"roi_per_bet":float("nan"),"brier":float("nan"),"logloss":float("nan")}
    n_total=len(df); m=df["y"].isin([0,1]); n_joined=int(m.sum()); n_pending=int(df["y"].isna().sum())
    roi_units=float(df.loc[m,"profit_units"].sum()) if "profit_units" in df.columns else float("nan")
    roi_per_bet=float(df.loc[m,"profit_units"].mean()) if ("profit_units" in df.columns and n_joined>0) else float("nan")
    p_col="p_cal" if "p_cal" in df.columns else ("p_raw" if "p_raw" in df.columns else None)
    if p_col:
        brier=safe_brier(df[p_col],df["y"]); logloss=safe_logloss(df[p_col],df["y"])
    else:
        brier=float("nan"); logloss=float("nan")
    return {"day":d,"n_total":int(n_total),"n_joined":int(n_joined),"n_pending":int(n_pending),"roi_units":roi_units,"roi_per_bet":roi_per_bet,"brier":brier,"logloss":logloss}
def trailing(daily,days):
    if daily.empty: return {"window":days,"n_joined":0,"roi_units":float("nan"),"roi_per_bet":float("nan"),"brier":float("nan"),"logloss":float("nan")}
    tail=daily.tail(days).copy()
    joined_mask=tail["n_joined"]>0
    w=tail.loc[joined_mask,"n_joined"]
    brier=float(np.average(tail.loc[joined_mask,"brier"],weights=w)) if joined_mask.any() else float("nan")
    logloss=float(np.average(tail.loc[joined_mask,"logloss"],weights=w)) if joined_mask.any() else float("nan")
    return {"window":days,"n_joined":int(tail["n_joined"].sum()),"roi_units":float(tail["roi_units"].sum()),"roi_per_bet":float((tail["roi_units"].sum()/tail["n_joined"].sum()) if tail["n_joined"].sum()>0 else float("nan")),"brier":brier,"logloss":logloss}
def main():
    p=argparse.ArgumentParser(description="Aggregate outcomes → daily metrics and trailing windows")
    p.add_argument("--outdir",default="outcomes"); p.add_argument("--artifact-dir",default="outcomes_rollup"); p.add_argument("--days",type=int,default=30)
    args=p.parse_args()
    os.makedirs(args.artifact_dir,exist_ok=True)
    paths=list_joined(args.outdir)
    if not paths:
        pd.DataFrame(columns=["day","n_total","n_joined","n_pending","roi_units","roi_per_bet","brier","logloss"]).to_csv(f"{args.artifact_dir}/metrics_daily.csv",index=False)
        open(f"{args.artifact_dir}/summary.txt","w").write("outcomes_rollup no-data\n")
        print("outcomes_rollup D=none n=0 joined=0 pending=0 roi=nan brier=nan logloss=nan t7_roi=nan t30_roi=nan")
        sys.exit(0)
    daily=pd.DataFrame([summarize_day(p) for p in paths])
    daily["day"]=pd.to_datetime(daily["day"])
    daily=daily.sort_values("day")
    daily.to_csv(f"{args.artifact_dir}/metrics_daily.csv",index=False)
    t7=trailing(daily,7); t30=trailing(daily,30)
    pd.DataFrame([t7,t30]).to_csv(f"{args.artifact_dir}/metrics_trailing.csv",index=False)
    idx=(daily["n_total"]>0) | (daily["n_joined"]>0)
    latest=(daily[idx].iloc[-1] if idx.any() else daily.iloc[-1]).to_dict()
    line=f"outcomes_rollup D={latest['day'].date()} n={int(latest['n_total'])} joined={int(latest['n_joined'])} pending={int(latest['n_pending'])} roi={(latest['roi_per_bet'] if not math.isnan(latest['roi_per_bet']) else float('nan')):+.3f} brier={(latest['brier'] if not math.isnan(latest['brier']) else float('nan')):.3f} logloss={(latest['logloss'] if not math.isnan(latest['logloss']) else float('nan')):.3f} t7_roi={t7['roi_units']:+.2f} t30_roi={t30['roi_units']:+.2f}"
    open(f"{args.artifact_dir}/summary.txt","w").write(line+"\n")
    print(line)
if __name__=="__main__": main()
