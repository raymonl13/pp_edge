#!/usr/bin/env python3
import os, csv, json
from pathlib import Path

def load_policy():
    try:
        import yaml
        y = yaml.safe_load(Path("ci/ev_policy.yaml").read_text())
        return y or {}
    except Exception:
        return {}

def read_csv(path):
    try:
        with open(path, newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []

def get_day():
    d=os.environ.get("DAY","")
    if d: return d
    import re
    files=sorted(Path(".").glob("edge_sheet_*.csv"))
    if not files: return ""
    m=re.match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", files[-1].name)
    return m.group(1) if m else ""

def main():
    day=get_day()
    pol = load_policy()
    bk = float(((pol.get("bankroll_policy") or {}).get("bankroll_base") or 10000.0))
    day_cap = float(((pol.get("bankroll_policy") or {}).get("day_cap_fraction") or 0.03))*bk
    slip_cap = float(((pol.get("bankroll_policy") or {}).get("slip_cap_fraction") or 0.01))*bk
    round_to = float(((pol.get("bankroll_policy") or {}).get("round_to") or 1.0))
    kelly = float(pol.get("kelly_fraction") or 0.25)
    explore = float(pol.get("explore_stake") or 0.0)
    ev_floor = float(pol.get("ev_floor") or 0.0)

    rd = next((p for p in Path(".").glob("qa_alloc_*") if p.is_dir()), None)
    alloc = "alloc_slips_with_stakes.csv"
    alloc_path = Path(alloc) if Path(alloc).exists() else (rd/alloc if rd else None)

    slips = read_csv(str(alloc_path)) if alloc_path and alloc_path.exists() else []
    # Aggregate by slip key
    by_key={}
    for r in slips:
        k=r.get("slip_key") or r.get("slip_id") or "slip_0"
        stake = r.get("stake") or r.get("wager") or "0"
        try: stake_f=float(stake)
        except: stake_f=0.0
        by_key.setdefault(k, {"stake":0.0, "type": r.get("slip_type")}).update(
            {"stake": by_key.get(k,{}).get("stake",0.0)+stake_f}
        )

    total_staked = sum(v["stake"] for v in by_key.values())
    remaining_day = max(0.0, day_cap - total_staked)

    advisories=[]
    for k,v in by_key.items():
        over_slip_cap = v["stake"] > slip_cap + 1e-9
        advisories.append({
            "slip_id": k,
            "type": v.get("type"),
            "stake_current": round(v["stake"],2),
            "stake_cap": round(slip_cap,2),
            "over_slip_cap": over_slip_cap
        })

    suggested_explore = 0.0 if explore<=0 else min(explore, remaining_day)
    out={
        "version":"1.0",
        "day":day,
        "bankroll_base": bk,
        "day_cap": round(day_cap,2),
        "slip_cap": round(slip_cap,2),
        "kelly_fraction": kelly,
        "ev_floor": ev_floor,
        "total_staked": round(total_staked,2),
        "remaining_day_cap": round(remaining_day,2),
        "suggested_explore_stake": round(suggested_explore,2),
        "slip_advisories": advisories
    }
    Path("risk_advisory.json").write_text(json.dumps(out,indent=2))
    print(f"[risk] day_cap={out['day_cap']} used={out['total_staked']} remain={out['remaining_day_cap']} slip_cap={out['slip_cap']}")
if __name__=="__main__":
    main()
