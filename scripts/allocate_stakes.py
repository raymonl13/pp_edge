#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
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
        for row in r: out.append(row)
    return out

def write_stakes(fp: Path, rows: List[Dict[str,Any]]) -> None:
    with fp.open("w", newline="") as f:
        w=csv.writer(f)
        w.writerow(["slip_id","slip_type","size","ev","ev_method","players","games","stake"])
        for r in rows:
            w.writerow([r["slip_id"], r["slip_type"], r["size"], r["ev"], r["ev_method"], r["players"], r["games"], f'{float(r["stake"]):.2f}'])

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x<lo else hi if x>hi else x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args=ap.parse_args()

    day = iso_day(args.day)
    cfg = load_cfg(Path(args.cfg))
    stakes_cfg = (cfg.get("stakes") or {})

    bankroll        = float(stakes_cfg.get("bankroll",        100.0))
    per_day_cap     = float(stakes_cfg.get("per_day_cap",       3.0))
    max_per_slip    = float(stakes_cfg.get("max_per_slip",      1.0))
    min_per_slip    = float(stakes_cfg.get("min_per_slip",      1.0))
    kelly_fraction  = float(stakes_cfg.get("kelly_fraction",    0.10))
    ev_floor        = float(stakes_cfg.get("ev_floor",         -1.00))
    max_slips       = int(stakes_cfg.get("max_slips",             2))
    explore_stake   = float(stakes_cfg.get("explore_stake",      1.0))  # CI default; set 0.0 in prod
    explore_top_k   = int(stakes_cfg.get("explore_top_k",         1))

    slips_csv = Path("alloc_slips.csv")
    out_csv   = Path("alloc_slips_with_stakes.csv")

    slips = read_slips(slips_csv)
    if not slips:
        write_stakes(out_csv, [])
        with open("run_meta.txt","a") as fh:
            fh.write("STAKES_ROWS=0\nSTAKES_TOTAL=0.00\nSTAKES_METHOD=ev_proportional\nSTAKES_EXPLORE=SKIPPED\n")
        print("STAKES_ROWS=0"); print("STAKES_TOTAL=0.00"); return

    # Parse & sort by EV desc
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

    picked=[]; total=0.0

    # Production-path: only positive EV
    for r in candidates:
        if len(picked) >= max_slips: break
        raw = bankroll * kelly_fraction * max(0.0, r["ev"])
        stake = clamp(raw, min_per_slip, max_per_slip) if raw > 0 else 0.0
        if stake <= 0: continue
        if total + stake > per_day_cap:
            rem = per_day_cap - total
            if rem >= min_per_slip:
                r2 = dict(r); r2["stake"] = rem
                picked.append(r2); total += rem
            break
        r2 = dict(r); r2["stake"] = stake
        picked.append(r2); total += stake

    # Explore fallback (CI only): tiny stake on top-K when nothing picked
    explore_flag = "SKIPPED"
    if not picked and candidates and explore_stake > 0.0:
        for r in candidates[:max(0, explore_top_k)]:
            if total >= per_day_cap: break
            stake = clamp(explore_stake, min_per_slip, max_per_slip)
            if total + stake > per_day_cap:
                rem = per_day_cap - total
                if rem < min_per_slip: break
                stake = rem
            r2 = dict(r); r2["stake"] = stake
            picked.append(r2); total += stake
        explore_flag = "USED" if picked else "SKIPPED"

    write_stakes(out_csv, picked)

    with open("run_meta.txt","a") as fh:
        fh.write(f"STAKES_ROWS={len(picked)}\n")
        fh.write(f"STAKES_TOTAL={total:.2f}\n")
        fh.write("STAKES_METHOD=ev_proportional\n")
        fh.write(f"STAKES_EXPLORE={explore_flag}\n")

    print(f"STAKES_ROWS={len(picked)}")
    print(f"STAKES_TOTAL={total:.2f}")

if __name__=="__main__":
    main()
