#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from typing import Dict, Any, List

def iso_day(day: str|None) -> str:
    if day: return day
    import datetime
    return (datetime.date.today()+datetime.timedelta(days=1)).isoformat()

def load_cfg(path: Path) -> Dict[str,Any]:
    if not path.exists(): return {}
    try:
        import yaml
        d = yaml.safe_load(path.read_text()) or {}
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}

def read_slips(fp: Path) -> List[Dict[str,Any]]:
    out=[]
    if not fp.exists(): return out
    with fp.open() as f:
        r=csv.DictReader(f)
        for row in r:
            out.append(row)
    return out

def write_stakes(fp: Path, rows: List[Dict[str,Any]]) -> None:
    with fp.open("w", newline="") as f:
        w=csv.writer(f)
        w.writerow(["slip_id","slip_type","size","ev","ev_method","players","games","stake"])
        for r in rows:
            w.writerow([r["slip_id"], r["slip_type"], r["size"], r["ev"], r["ev_method"], r["players"], r["games"], f'{float(r["stake"]):.2f}'])

def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo: return lo
    if x > hi: return hi
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args=ap.parse_args()

    day = iso_day(args.day)
    cfg = load_cfg(Path(args.cfg))
    stakes_cfg = (cfg.get("stakes") or {})

    bankroll        = float(stakes_cfg.get("bankroll",        100.0))
    per_day_cap     = float(stakes_cfg.get("per_day_cap",      25.0))
    max_per_slip    = float(stakes_cfg.get("max_per_slip",     10.0))
    min_per_slip    = float(stakes_cfg.get("min_per_slip",      1.0))
    kelly_fraction  = float(stakes_cfg.get("kelly_fraction",    0.10))
    ev_floor        = float(stakes_cfg.get("ev_floor",          0.00))
    max_slips       = int(stakes_cfg.get("max_slips",              5))

    slips_csv = Path(f"alloc_slips.csv")
    out_csv   = Path(f"alloc_slips_with_stakes.csv")

    slips = read_slips(slips_csv)
    if not slips:
        # seed empty artifact + meta; do not fail the job
        write_stakes(out_csv, [])
        with open("run_meta.txt","a") as fh:
            fh.write("STAKES_ROWS=0\n")
            fh.write("STAKES_TOTAL=0.00\n")
            fh.write("STAKES_METHOD=ev_proportional\n")
        print("STAKES_ROWS=0")
        return

    # Parse, filter by EV floor, sort by EV desc
    parsed=[]
    for r in slips:
        try:
            ev=float(r.get("ev",0.0))
            size=int(float(r.get("size",0)))
        except Exception:
            ev=0.0; size=0
        parsed.append({**r, "ev":ev, "size":size})
    candidates=[r for r in parsed if r["ev"] >= ev_floor]
    candidates.sort(key=lambda x: x["ev"], reverse=True)

    # EV-proportional stake suggestion; clamp per slip; respect day cap and max_slips
    picked=[]
    total=0.0
    for r in candidates:
        if len(picked) >= max_slips: break
        # proportional to EV; safe, small Kelly-like fraction
        raw = bankroll * kelly_fraction * max(0.0, r["ev"])
        stake = clamp(raw, min_per_slip, max_per_slip) if raw > 0 else 0.0
        if stake <= 0: continue
        if total + stake > per_day_cap:
            # fit the remainder if still >= min stake; else skip
            rem = per_day_cap - total
            if rem >= min_per_slip:
                r2 = dict(r)
                r2["stake"] = rem
                picked.append(r2)
                total += rem
            break
        r2 = dict(r)
        r2["stake"] = stake
        picked.append(r2)
        total += stake

    # If nothing picked due to caps, still output header-only with 0 rows (non-fatal)
    write_stakes(out_csv, picked)

    # meta
    with open("run_meta.txt","a") as fh:
        fh.write(f"STAKES_ROWS={len(picked)}\n")
        fh.write(f"STAKES_TOTAL={total:.2f}\n")
        fh.write("STAKES_METHOD=ev_proportional\n")

    print(f"STAKES_ROWS={len(picked)}")
    print(f"STAKES_TOTAL={total:.2f}")

if __name__=="__main__":
    main()
