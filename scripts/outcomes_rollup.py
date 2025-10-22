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
    except Exception: 
        return {"day":d,"n_total":0,"n_joined":0,"n_pending":0,"roi_units":float("nan"),"roi_per_bet":float("nan"),
                "brier_raw":float("nan"),"logloss_raw":float("nan"),"brier_cal":float("nan"),"logloss_cal":float("nan")}
    n_total=len(df); m=df["y"].isin([0,1]); n_joined=int(m.sum()); n_pending=int(df["y"].isna().sum())
    roi_units=float(df.loc[m,"profit_units"].sum()) if "profit_units" in df.columns else float("nan")
    roi_per_bet=float(df.loc[m,"profit_units"].mean()) if ("profit_units" in df.columns and n_joined>0) else float("nan")
    br_raw=ll_raw=br_cal=ll_cal=float("nan")
    if "p_raw" in df.columns:
        br_raw=safe_brier(df["p_raw"],df["y"])
        ll_raw=safe_logloss(df["p_raw"],df["y"])
    if "p_cal" in df.columns:
        br_cal=safe_brier(df["p_cal"],df["y"])
        ll_cal=safe_logloss(df["p_cal"],df["y"])
    return {"day":d,"n_total":int(n_total),"n_joined":int(n_joined),"n_pending":int(n_pending),
            "roi_units":roi_units,"roi_per_bet":roi_per_bet,
            "brier_raw":br_raw,"logloss_raw":ll_raw,"brier_cal":br_cal,"logloss_cal":ll_cal}
def trailing(daily,days):
    if daily.empty: 
        return {"window":days,"n_joined":0,"roi_units":float("nan"),"roi_per_bet":float("nan"),
                "brier_raw":float("nan"),"logloss_raw":float("nan"),"brier_cal":float("nan"),"logloss_cal":float("nan")}
    tail=daily.tail(days).copy()
    joined_mask=tail["n_joined"]>0
    w=tail.loc[joined_mask,"n_joined"]
    br_raw=float(np.average(tail.loc[joined_mask,"brier_raw"],weights=w)) if joined_mask.any() else float("nan")
    ll_raw=float(np.average(tail.loc[joined_mask,"logloss_raw"],weights=w)) if joined_mask.any() else float("nan")
    br_cal=float(np.average(tail.loc[joined_mask,"brier_cal"],weights=w)) if joined_mask.any() else float("nan")
    ll_cal=float(np.average(tail.loc[joined_mask,"logloss_cal"],weights=w)) if joined_mask.any() else float("nan")
    return {"window":days,"n_joined":int(tail["n_joined"].sum()),
            "roi_units":float(tail["roi_units"].sum()),
            "roi_per_bet":float((tail["roi_units"].sum()/tail["n_joined"].sum()) if tail["n_joined"].sum()>0 else float("nan")),
            "brier_raw":br_raw,"logloss_raw":ll_raw,"brier_cal":br_cal,"logloss_cal":ll_cal}
def main():
    p=argparse.ArgumentParser(description="Aggregate outcomes → daily metrics and trailing windows")
    p.add_argument("--outdir",default="outcomes"); p.add_argument("--artifact-dir",default="outcomes_rollup"); p.add_argument("--days",type=int,default=30)
    args=p.parse_args()
    os.makedirs(args.artifact_dir,exist_ok=True)
    paths=list_joined(args.outdir)
    if not paths:
        pd.DataFrame(columns=["day","n_total","n_joined","n_pending","roi_units","roi_per_bet","brier_raw","logloss_raw","brier_cal","logloss_cal"]).to_csv(f"{args.artifact_dir}/metrics_daily.csv",index=False)
        open(f"{args.artifact_dir}/summary.txt","w").write("outcomes_rollup no-data\n")
        print("outcomes_rollup D=none n=0 joined=0 pending=0 roi=nan brier_raw=nan brier_cal=nan logloss_raw=nan logloss_cal=nan t7_roi=nan t30_roi=nan")
        sys.exit(0)
    daily=pd.DataFrame([summarize_day(pth) for pth in paths])
    daily["day"]=pd.to_datetime(daily["day"]); daily=daily.sort_values("day")
    daily.to_csv(f"{args.artifact_dir}/metrics_daily.csv",index=False)
    t7=trailing(daily,7); t30=trailing(daily,30)
    pd.DataFrame([t7,t30]).to_csv(f"{args.artifact_dir}/metrics_trailing.csv",index=False)
    idx=(daily["n_total"]>0)|(daily["n_joined"]>0)
    latest=(daily[idx].iloc[-1] if idx.any() else daily.iloc[-1]).to_dict()
    dlt_br=(latest["brier_raw"]-latest["brier_cal"]) if (not math.isnan(latest.get("brier_raw",float("nan")) or float("nan")) and not math.isnan(latest.get("brier_cal",float("nan")) or float("nan"))) else float("nan")
    dlt_ll=(latest["logloss_raw"]-latest["logloss_cal"]) if (not math.isnan(latest.get("logloss_raw",float("nan")) or float("nan")) and not math.isnan(latest.get("logloss_cal",float("nan")) or float("nan"))) else float("nan")
    line=f"outcomes_rollup D={latest['day'].date()} n={int(latest['n_total'])} joined={int(latest['n_joined'])} pending={int(latest['n_pending'])} roi={(latest['roi_per_bet'] if not math.isnan(latest['roi_per_bet']) else float('nan')):+.3f} brier_raw={(latest['brier_raw'] if not math.isnan(latest['brier_raw']) else float('nan')):.3f} brier_cal={(latest['brier_cal'] if not math.isnan(latest['brier_cal']) else float('nan')):.3f} dbrier={(dlt_br if not math.isnan(dlt_br) else float('nan')):+.3f} logloss_raw={(latest['logloss_raw'] if not math.isnan(latest['logloss_raw']) else float('nan')):.3f} logloss_cal={(latest['logloss_cal'] if not math.isnan(latest['logloss_cal']) else float('nan')):.3f} dlogloss={(dlt_ll if not math.isnan(dlt_ll) else float('nan')):+.3f} t7_roi={t7['roi_units']:+.2f} t30_roi={t30['roi_units']:+.2f}"
    open(f"{args.artifact_dir}/summary.txt","w").write(line+"\n")
    print(line)
if __name__=="__main__":
    main()
