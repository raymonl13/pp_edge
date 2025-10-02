#!/usr/bin/env python3
from __future__ import annotations
import csv, itertools, json, math
from pathlib import Path
from typing import Dict, Any, List, Tuple

def iso_day(day: str|None) -> str:
    if day: return day
    import datetime
    return (datetime.date.today()+datetime.timedelta(days=1)).isoformat()

def nCr(n:int, r:int)->int:
    if r<0 or r>n: return 0
    r=min(r, n-r); numer=1; denom=1
    for i in range(r):
        numer*= (n-i); denom*= (i+1)
    return numer//denom

def read_cfg(path: Path) -> Dict[str,Any]:
    if not path.exists(): return {}
    try:
        import yaml
        with path.open() as f:
            d=yaml.safe_load(f) or {}
            return d if isinstance(d,dict) else {}
    except Exception:
        return {}

def read_legs(edge_csv: Path) -> List[Dict[str,Any]]:
    out=[]
    if not edge_csv.exists(): return out
    with edge_csv.open() as f:
        r=csv.DictReader(f)
        for row in r:
            try:
                out.append({
                    "player": row["player"],
                    "game_id": row["game_id"],
                    "p_hit": float(row["p_hit"]),
                    "edge_pp": float(row["edge_pp"]),
                    "tier": row["tier"],
                    "slip_type": row["slip_type"],
                })
            except Exception:
                continue
    return out

def slip_sizes(payouts: Dict[str,Any]) -> Dict[str,int]:
    sizes={}
    for k in payouts.keys():
        if k.startswith("Power"):
            try: sizes[k]=int(k.replace("Power",""))
            except: pass
        elif k.startswith("Flex"):
            try: sizes[k]=int(k.replace("Flex",""))
            except: pass
    return sizes

def combos_after_guard(pool: List[Dict[str,Any]], size:int, cap:int=50000) -> Tuple[int,int]:
    n=len(pool)
    total=nCr(n,size)
    built=0
    if total==0: return total,0
    # Enumerate exactly for small totals; otherwise sample up to cap
    limit=min(total, cap)
    it=itertools.combinations(pool, size)
    i=0
    for combo in it:
        i+=1
        players=[c["player"] for c in combo]
        games=[c["game_id"] for c in combo]
        if len(players)==len(set(players)) and len(games)==len(set(games)):
            built+=1
        if i>=limit: break
    if total>cap:
        # scale up estimate; conservative floor
        built=int(built * (total/limit))
    return total, built

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args=ap.parse_args()
    day=iso_day(args.day)
    edge_csv=Path(f"edge_sheet_{day}.csv")
    cfg=read_cfg(Path(args.cfg))
    payouts=cfg.get("payouts") or {"Power2":3.0,"Power3":5.0,"Power4":10.0,"Power6":25.0,"Flex4":{"4":1.5,"3":0.5},"Flex5":{"5":10.0,"4":2.0}}
    sizes=slip_sizes(payouts)
    legs=read_legs(edge_csv)
    # observed keys present in the legs
    observed=[]
    seen=set()
    for l in legs:
        st=l["slip_type"]
        if st not in seen:
            observed.append(st); seen.add(st)
    # per-type diagnostics
    diag={"day":day,"types":[]}
    for st in sorted(set(list(payouts.keys())+observed)):
        pool=[l for l in legs if l["slip_type"]==st]
        n=len(pool)
        sz=sizes.get(st,0)
        uniq_players=len({l["player"] for l in pool})
        uniq_games=len({l["game_id"] for l in pool})
        reason=[]
        if sz==0:
            reason.append("no_size_for_type")
        if n<sz:
            reason.append(f"insufficient_pool:{n}<{sz}")
        total,built=(0,0)
        if sz>0 and n>=sz:
            total,built=combos_after_guard(pool, sz, cap=200000)
            if built==0 and total>0:
                reason.append("guard_eliminated_all")
        diag["types"].append({
            "slip_type": st,
            "required_size": sz,
            "pool_size": n,
            "uniq_players": uniq_players,
            "uniq_games": uniq_games,
            "total_combos": total,
            "built_combos": built,
            "reason": reason,
        })
    # write artifacts
    Path("slip_diag.json").write_text(json.dumps(diag, indent=2))
    with open("slip_diag.txt","w") as f:
        for t in diag["types"]:
            f.write(f"{t['slip_type']}: pool={t['pool_size']} size={t['required_size']} uniqP={t['uniq_players']} uniqG={t['uniq_games']} total={t['total_combos']} built={t['built_combos']} reason={';'.join(t['reason']) or 'ok'}\n")
    # meta shorthand
    lines=[]
    lines.append("SLIP_DIAG_TYPES=" + ",".join([t["slip_type"] for t in diag["types"]]))
    for t in diag["types"]:
        lines.append(f"SLIP_DIAG_{t['slip_type']}=pool:{t['pool_size']}/size:{t['required_size']}/uniqP:{t['uniq_players']}/uniqG:{t['uniq_games']}/combos:{t['built_combos']}/{t['total_combos']}/reason:{';'.join(t['reason']) or 'ok'}")
    with open("run_meta.txt","a") as fh:
        for ln in lines: fh.write(ln+"\n")
    print("SLIP_DIAG_DONE")
if __name__=="__main__":
    main()
