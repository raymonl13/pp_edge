#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, itertools, json
from pathlib import Path
from typing import Dict, Any, List, Tuple

def iso_day(day: str | None) -> str:
    if day: return day
    import datetime
    return (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

def load_cfg(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists(): return {}
    try:
        import yaml
        with p.open() as f: d = yaml.safe_load(f) or {}
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}

def read_legs(csv_path: Path) -> List[Dict[str,Any]]:
    out=[]
    if not csv_path.exists(): return out
    with csv_path.open(newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                out.append({
                    "player": (row["player"] or "").strip(),
                    "game_id": (row["game_id"] or "").strip(),
                    "p_hit": float(row["p_hit"]),
                    "edge_pp": float(row["edge_pp"]),
                    "tier": (row["tier"] or "").strip(),
                    "slip_type": (row["slip_type"] or "").strip(),
                })
            except Exception:
                continue
    return out

def choose_slip_sizes(payouts: Dict[str,Any]) -> Dict[str,int]:
    sizes={}
    for k in payouts.keys():
        if k.startswith("Power"):
            try: sizes[k]=int(k.replace("Power",""))
            except: pass
        elif k.startswith("Flex"):
            try: sizes[k]=int(k.replace("Flex",""))
            except: pass
    return sizes

def power_ev(ps: List[float], payout: float) -> float:
    prod=1.0
    for p in ps: prod*=p
    return prod*payout - 1.0

def flex_ev(ps: List[float], payout_map: Dict[str,float]) -> float:
    n=len(ps); ev=0.0
    for h_s, mult in payout_map.items():
        try: h=int(h_s)
        except: continue
        if h<0 or h>n: continue
        s=0.0
        for combo in itertools.combinations(range(n), h):
            pr=1.0
            for i in range(n):
                pr*= ps[i] if i in combo else (1.0-ps[i])
            s+=pr
        ev+= s*float(mult)
    return ev - 1.0

def combo_ev(ps: List[float], slip_type: str, payouts: Dict[str,Any]) -> Tuple[float,str]:
    v=payouts.get(slip_type)
    if isinstance(v,(int,float)):
        return power_ev(ps,float(v)),"all_must_hit"
    if isinstance(v,dict):
        return flex_ev(ps,{str(k):float(vv) for k,vv in v.items()}),"combo_exact"
    return power_ev(ps,1.0),"unknown"

def unique_players_only(players: List[str]) -> bool:
    return len(players)==len(set(players))

def rank_legs(legs: List[Dict[str,Any]], max_pool: int) -> List[Dict[str,Any]]:
    return sorted(legs, key=lambda x: (x.get("edge_pp",0.0), x.get("p_hit",0.0)), reverse=True)[:max_pool]

def build_for_type(legs_by_type: List[Dict[str,Any]], size: int, slip_type: str, payouts: Dict[str,Any], max_slips: int) -> List[Dict[str,Any]]:
    legs=rank_legs(legs_by_type, max_pool=200)
    out=[]; seen=set()
    for combo in itertools.combinations(legs, size):
        players=[c["player"] for c in combo]
        if not unique_players_only(players): continue
        ps=[max(1e-6,min(1-1e-6,c["p_hit"])) for c in combo]
        ev,method=combo_ev(ps, slip_type, payouts)
        slip_id="slip-"+str(abs(hash(tuple([(c["player"],c["game_id"],slip_type) for c in combo]))))[:12]
        if slip_id in seen: continue
        seen.add(slip_id)
        out.append({
            "slip_id": slip_id,
            "slip_type": slip_type,
            "size": size,
            "ev": round(ev,6),
            "ev_method": method,
            "legs": [{"player":c["player"],"game_id":c["game_id"],"p_hit":round(c["p_hit"],6),"edge_pp":round(c["edge_pp"],6),"tier":c["tier"]} for c in combo],
        })
        if len(out)>=max_slips: break
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args=ap.parse_args()
    day=iso_day(args.day)
    csv_path=Path(f"edge_sheet_{day}.csv")
    if not csv_path.exists():
        with open("run_meta.txt","a") as fh:
            fh.write("SLIPS_BUILT=0\n")
            fh.write("SLIP_KEYS_METHOD=none\n")
            fh.write("SLIP_EV_METHOD=none\n")
            fh.write("SLIP_KEYS_OBSERVED=NONE\n")
        print("SLIPS_BUILT=0"); return

    cfg=load_cfg(args.cfg)
    payouts=cfg.get("payouts") or {"Power2":3.0,"Power3":5.0,"Power4":10.0,"Power6":25.0,"Flex4":{"4":1.5,"3":0.5},"Flex5":{"5":10.0,"4":2.0}}
    slip_cfg=cfg.get("slips") or {}
    prefer=[str(x).strip() for x in (slip_cfg.get("slip_types") or ["Power2","Power3"])]
    max_types=int(slip_cfg.get("max_types",2))
    max_slips_per_type=int(slip_cfg.get("max_slips_per_type",5))
    sizes=choose_slip_sizes(payouts)

    legs=read_legs(csv_path)
    legs=[l for l in legs if 0.0<=l["p_hit"]<=1.0]

    observed=[]; seen=set()
    for l in legs:
        st=l["slip_type"]
        if st not in seen:
            observed.append(st); seen.add(st)

    pools={t:[l for l in legs if l["slip_type"]==t] for t in set(observed + list(payouts.keys()))}
    pool_sizes={t:len(pools[t]) for t in pools}
    req_sizes={t:sizes.get(t,0) for t in pools}

    cand=list(dict.fromkeys(prefer + [t for t in observed if t not in prefer]))
    feasible=[t for t in cand if req_sizes.get(t,0)>0 and pool_sizes.get(t,0)>=req_sizes.get(t,0)]
    selected=feasible[:max_types]
    skipped=[t for t in cand if t not in selected]

    slips=[]
    for st in selected:
        size=req_sizes.get(st,0)
        pool=pools.get(st,[])
        if size and len(pool)>=size:
            slips.extend(build_for_type(pool, size, st, payouts, max_slips_per_type))

    # feasibility fallback: if nothing built, force first feasible observed type
    if not slips:
        obs_feasible=[t for t in observed if req_sizes.get(t,0)>0 and pool_sizes.get(t,0)>=req_sizes.get(t,0)]
        if obs_feasible:
            fb=obs_feasible[0]
            size=req_sizes.get(fb,0)
            pool=pools.get(fb,[])
            if size and len(pool)>=size:
                slips.extend(build_for_type(pool, size, fb, payouts, max_slips=1))
                selected=[fb]
                skipped=[t for t in cand if t!=fb]
                prefer=[]  # method → 'fallback'

    slips_sorted=sorted(slips, key=lambda x: x["ev"], reverse=True)

    debug={
        "day": day,
        "prefer": prefer,
        "observed": observed,
        "pool_sizes": pool_sizes,
        "req_sizes": req_sizes,
        "cand": cand,
        "feasible": feasible,
        "selected": selected,
        "skipped": skipped,
        "slips_built": len(slips_sorted)
    }
    Path("slip_builder_debug.json").write_text(json.dumps(debug, indent=2))

    Path("slips.json").write_text(json.dumps({"day":day,"slips":slips_sorted}, separators=(",",":")))
    with open("alloc_slips.csv","w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["slip_id","slip_type","size","ev","ev_method","players","games"])
        for s in slips_sorted:
            players="|".join([l["player"] for l in s["legs"]])
            games="|".join([l["game_id"] for l in s["legs"]])
            w.writerow([s["slip_id"],s["slip_type"],s["size"],s["ev"],s["ev_method"],players, games])

    with open("run_meta.txt","a") as fh:
        fh.write(f"SLIPS_BUILT={len(slips_sorted)}\n")
        method='fallback' if slips_sorted and selected and selected[0] not in prefer else ('prefer' if selected and selected[0] in prefer else ('observed' if selected else 'none'))
        fh.write(f"SLIP_KEYS_METHOD={method}\n")
        fh.write(f"SLIP_EV_METHOD={(slips_sorted[0]['ev_method'] if slips_sorted else 'none')}\n")
        fh.write(f"SLIP_KEYS_OBSERVED={','.join(observed) if observed else 'NONE'}\n")
        fh.write(f"SLIP_KEYS_SELECTED={','.join(selected) if selected else 'NONE'}\n")
        if skipped:
            reasons=[]
            for t in skipped:
                rs=req_sizes.get(t,0); ps=pool_sizes.get(t,0)
                if rs==0: reasons.append(f"{t}:no_size")
                elif ps<rs: reasons.append(f"{t}:pool{ps}<{rs}")
                else: reasons.append(f"{t}:deprioritized")
            fh.write("SLIP_KEYS_SKIPPED="+";".join(reasons)+"\n")

    print(f"SLIPS_BUILT={len(slips_sorted)}")
