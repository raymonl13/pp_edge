#!/usr/bin/env python3
import os, csv, json, math
from pathlib import Path

def get_day():
    d=os.environ.get("DAY","")
    if d: return d
    import re
    files=sorted(Path(".").glob("edge_sheet_*.csv"))
    if not files: return ""
    m=re.match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", files[-1].name)
    return m.group(1) if m else ""

def read_csv(path):
    try:
        with open(path, newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []

def safe_float(x):
    try: return float(x)
    except Exception: return None

def main():
    day=get_day()
    edge=f"edge_sheet_{day}.csv" if day else None
    rows = read_csv(edge) if edge and Path(edge).exists() else []
    preds = {}
    for r in rows:
        pid = r.get("leg_id") or r.get("player_id") or r.get("row_id") or None
        p = r.get("pred_hit_prob") or r.get("p_hit") or r.get("prob")
        pf = safe_float(p)
        if pid and pf is not None:
            preds[str(pid)]=pf

    realized_path = Path(f"realized/realized_{day}.csv")
    realized = read_csv(realized_path) if realized_path.exists() else []
    have_realized = len(realized)>0

    eps=1e-12
    n=0; brier_sum=0.0; logloss_sum=0.0
    stake_sum=0.0; payout_sum=0.0
    logs=[]
    for r in realized:
        pid = str(r.get("leg_id") or r.get("player_id") or "")
        y = r.get("outcome")  # 1/0
        yv = safe_float(y)
        p = preds.get(pid, None)
        st = safe_float(r.get("stake") or 0)
        po = safe_float(r.get("payout") or 0)
        if yv in (0.0,1.0) and p is not None:
            n+=1
            brier_sum += (p - yv)**2
            logloss_sum += - ( yv*math.log(max(p,eps)) + (1-yv)*math.log(max(1-p,eps)) )
        stake_sum += st or 0.0
        payout_sum += po or 0.0
        logs.append({"leg_id":pid,"p":p,"y":yv,"stake":st,"payout":po})

    metrics={
        "day": day,
        "count_scored": n,
        "brier": (brier_sum/n if n>0 else None),
        "logloss": (logloss_sum/n if n>0 else None),
        "stake_total": round(stake_sum,2),
        "payout_total": round(payout_sum,2),
        "roi": ( (payout_sum - stake_sum)/stake_sum if stake_sum>0 else None),
        "status": ("COMPLETE" if have_realized else "PENDING")
    }

    outdir=Path("outcomes"); outdir.mkdir(exist_ok=True)
    jl=outdir/f"outcomes_{day}.jsonl"
    csvp=outdir/f"outcomes_{day}.csv"
    with jl.open("a") as f:
        f.write(json.dumps(metrics)+"\n")
    with csvp.open("w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(metrics.keys()))
        w.writeheader(); w.writerow(metrics)
    Path("outcomes_summary.json").write_text(json.dumps(metrics,indent=2))
    print(f"[outcomes] status={metrics['status']} n={n} roi={metrics['roi']}")
if __name__=="__main__":
    main()
