#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from typing import Dict, Any, List, Optional

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

def read_slips_csv(fp: Path) -> List[Dict[str,Any]]:
    out=[]
    if not fp.exists(): return out
    with fp.open() as f:
        r=csv.DictReader(f)
        for row in r: out.append(row)
    return out

def read_slips_json(fp: Path) -> Dict[str,Any]:
    if not fp.exists(): return {}
    try:
        return json.loads(fp.read_text())
    except Exception:
        return {}

def write_stakes(fp: Path, rows: List[Dict[str,Any]]) -> None:
    with fp.open("w", newline="") as f:
        w=csv.writer(f)
        w.writerow(["slip_id","slip_type","size","ev","ev_method","players","games","stake"])
        for r in rows:
            w.writerow([r["slip_id"], r["slip_type"], r["size"], r["ev"], r["ev_method"], r["players"], r["games"], f'{float(r["stake"]):.2f}'])

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x<lo else hi if x>hi else x

def kelly_power(stype: str, payout_map: Dict[str,Any], legs: List[Dict[str,Any]]) -> Optional[float]:
    """
    Returns Kelly fraction f* for Power slips (all must hit), or None if not applicable.
    Assumes independence: p_combo = ∏ p_i; decimal payout P => b=P−1; f*=(b·p − (1−p))/b.
    """
    if not stype.startswith("Power"): return None
    v = payout_map.get(stype)
    try:
        P = float(v)
        b = P - 1.0
        if b <= 0: return 0.0
        p = 1.0
        for leg in legs:
            p_i = float(leg.get("p_hit", 0.0))
            if not (0.0 < p_i < 1.0): return 0.0
            p *= p_i
        q = 1.0 - p
        f = (b * p - q) / b
        return max(0.0, f)
    except Exception:
        return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args=ap.parse_args()

    day = iso_day(args.day)
    cfg = load_cfg(Path(args.cfg))
    payouts = cfg.get("payouts") or {}
    stakes_cfg = (cfg.get("stakes") or {})

    method          = str(stakes_cfg.get("method","ev_proportional")).strip().lower()
    bankroll        = float(stakes_cfg.get("bankroll",        100.0))
    per_day_cap     = float(stakes_cfg.get("per_day_cap",       3.0))
    max_per_slip    = float(stakes_cfg.get("max_per_slip",      1.0))
    min_per_slip    = float(stakes_cfg.get("min_per_slip",      1.0))
    kelly_fraction  = float(stakes_cfg.get("kelly_fraction",    0.10))  # fraction-of-Kelly
    ev_floor        = float(stakes_cfg.get("ev_floor",         -1.00))
    max_slips       = int(stakes_cfg.get("max_slips",             2))
    explore_stake   = float(stakes_cfg.get("explore_stake",      1.0))  # CI default; set 0.0 in prod
    explore_top_k   = int(stakes_cfg.get("explore_top_k",         1))

    csv_in = Path("alloc_slips.csv")
    json_in= Path("slips.json")
    csv_out= Path("alloc_slips_with_stakes.csv")

    slips = read_slips_csv(csv_in)
    if not slips:
        write_stakes(csv_out, [])
        with open("run_meta.txt","a") as fh:
            fh.write("STAKES_ROWS=0\nSTAKES_TOTAL=0.00\nSTAKES_METHOD=none\nSTAKES_EXPLORE=SKIPPED\n")
        print("STAKES_ROWS=0"); print("STAKES_TOTAL=0.00"); return

    # Map slip_id -> legs from slips.json (if present)
    sj = read_slips_json(json_in)
    slip_legs: Dict[str, List[Dict[str,Any]]] = {}
    try:
        for s in (sj.get("slips") or []):
            sid = str(s.get("slip_id",""))
            if sid: slip_legs[sid] = s.get("legs") or []
    except Exception:
        slip_legs = {}

    # Parse CSV and prep candidates
    parsed=[]
    for r in slips:
        try:
            ev = float(r.get("ev", 0.0))
            size = int(float(r.get("size", 0)))
        except Exception:
            ev = 0.0; size = 0
        parsed.append({**r, "ev":ev, "size":size})
    candidates=[r for r in parsed if r["ev"] >= ev_floor]
    # primary sort key will depend on method below

    picked=[]; total=0.0; explore_flag="SKIPPED"
    method_used = "ev_proportional"

    if method == "kelly_combo":
        # compute Kelly fractions where possible; else fall back per-slip
        krows=[]
        for r in candidates:
            sid = r["slip_id"]; stype = str(r["slip_type"])
            legs = slip_legs.get(sid, [])
            f = kelly_power(stype, payouts, legs)
            if f is None:
                # Not applicable (e.g., Flex), or missing data -> mark fallback later
                r2 = dict(r); r2["_kelly"]=None; krows.append(r2)
            else:
                r2 = dict(r); r2["_kelly"]=float(f); krows.append(r2)
        # Sort by Kelly fraction desc (None -> last)
        krows.sort(key=lambda x: (x["_kelly"] is not None, x.get("_kelly",0.0)), reverse=True)

        # Allocate by Kelly fraction
        for r in krows:
            if len(picked) >= max_slips: break
            f = r.get("_kelly")
            if f is None or f <= 0.0:
                continue
            raw = bankroll * kelly_fraction * f
            stake = clamp(raw, min_per_slip, max_per_slip)
            if stake <= 0: continue
            if total + stake > per_day_cap:
                rem = per_day_cap - total
                if rem >= min_per_slip:
                    r2 = dict(r); r2["stake"]=rem; picked.append(r2); total+=rem
                break
            r2 = dict(r); r2["stake"]=stake; picked.append(r2); total+=stake

        method_used = "kelly_combo"

        # If Kelly picked nothing, degrade to EV-proportional (then explore)
        if not picked:
            candidates.sort(key=lambda x: x["ev"], reverse=True)
            for r in candidates:
                if len(picked) >= max_slips: break
                raw = bankroll * kelly_fraction * max(0.0, r["ev"])
                stake = clamp(raw, min_per_slip, max_per_slip) if raw>0 else 0.0
                if stake <= 0: continue
                if total + stake > per_day_cap:
                    rem = per_day_cap - total
                    if rem >= min_per_slip:
                        r2 = dict(r); r2["stake"]=rem; picked.append(r2); total+=rem
                    break
                r2 = dict(r); r2["stake"]=stake; picked.append(r2); total+=stake
            if picked:
                method_used += "+fallback_ev"

    else:
        # Legacy EV-proportional path
        candidates.sort(key=lambda x: x["ev"], reverse=True)
        for r in candidates:
            if len(picked) >= max_slips: break
            raw = bankroll * kelly_fraction * max(0.0, r["ev"])
            stake = clamp(raw, min_per_slip, max_per_slip) if raw>0 else 0.0
            if stake <= 0: continue
            if total + stake > per_day_cap:
                rem = per_day_cap - total
                if rem >= min_per_slip:
                    r2 = dict(r); r2["stake"]=rem; picked.append(r2); total+=rem
                break
            r2 = dict(r); r2["stake"]=stake; picked.append(r2); total+=stake
        method_used = "ev_proportional"

    # Explore fallback (CI only): tiny stake on top-K when nothing picked
    if not picked and candidates and explore_stake > 0.0:
        for r in candidates[:max(0, int(stakes_cfg.get("explore_top_k",1)))]:
            if total >= per_day_cap: break
            stake = clamp(explore_stake, min_per_slip, max_per_slip)
            if total + stake > per_day_cap:
                rem = per_day_cap - total
                if rem < min_per_slip: break
                stake = rem
            r2 = dict(r); r2["stake"] = stake
            picked.append(r2); total += stake
        explore_flag = "USED" if picked else "SKIPPED"

    write_stakes(csv_out, picked)

    with open("run_meta.txt","a") as fh:
        fh.write(f"STAKES_ROWS={len(picked)}\n")
        fh.write(f"STAKES_TOTAL={total:.2f}\n")
        fh.write(f"STAKES_METHOD={method_used}\n")
        fh.write(f"STAKES_EXPLORE={explore_flag}\n")

    print(f"STAKES_ROWS={len(picked)}")
    print(f"STAKES_TOTAL={total:.2f}")

if __name__=="__main__":
    main()
