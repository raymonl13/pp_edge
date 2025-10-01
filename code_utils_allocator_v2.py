#!/usr/bin/env python3
import csv,argparse,datetime
from pathlib import Path
from typing import Dict,Any,List
ALLOC_VERSION="4.1.0"
REQUIRED_COLS=("player","game_id","p_hit","edge_pp","tier","slip_type")
def _load_yaml(path:Path)->Dict[str,Any]:
    import yaml
    return yaml.safe_load(path.read_text()) or {}
def _read_edges(path:Path)->List[Dict[str,Any]]:
    rows=[]
    with path.open(newline="") as fh:
        rdr=csv.DictReader(fh)
        fn=rdr.fieldnames or []
        missing=[c for c in REQUIRED_COLS if c not in fn]
        if missing: raise SystemExit(f"missing required columns: {missing}")
        for r in rdr: rows.append(r)
    return rows
def _to_float(x,default=float("nan"))->float:
    try: return float(x)
    except Exception: return default
def allocate(rows:List[Dict[str,Any]],cfg:Dict[str,Any])->List[Dict[str,Any]]:
    a_cfg=cfg.get("allocator",{}) or {}
    t_mult=(cfg.get("tiers",{}) or {}).get("kelly_multiplier",{}) or {}
    bankroll=float(a_cfg.get("starting",1000.0))
    slip_cap=float(a_cfg.get("slip_cap",25.0))
    slate_cap_frac=float(a_cfg.get("slate_cap_frac",0.1))
    base_kelly=float(a_cfg.get("kelly_fraction",0.5))
    min_stake=float(a_cfg.get("min_stake",0.0))
    slate_cap=max(0.0,bankroll*slate_cap_frac)
    allocated_total=0.0
    out=[]
    def keyf(r):
        e=_to_float(r.get("edge_pp"))
        p=_to_float(r.get("p_hit"))
        name=r.get("player","")
        return (0 if e==e else 1,-e if e==e else 0,0 if p==p else 1,-p if p==p else 0,name)
    for r in sorted(rows,key=keyf):
        p=_to_float(r.get("p_hit"))
        edge=_to_float(r.get("edge_pp"))
        tier=r.get("tier","Standard")
        mult=float(t_mult.get(tier,1.0))
        if not (p==p and edge==edge) or p<=0.0 or p>1.0:
            stake=0.0
        else:
            b=(edge+1.0)/max(p,1e-9)
            q=1.0-p
            k_full=(b*p-q)/max(b,1e-9)
            k_used=max(0.0,min(1.0,k_full))*base_kelly*mult
            stake=min(slip_cap,bankroll*k_used)
        if allocated_total+stake>slate_cap:
            stake=max(0.0,slate_cap-allocated_total)
        if 0<stake<min_stake: stake=0.0
        allocated_total+=stake
        o=dict(r); o["stake"]=round(stake,2); out.append(o)
    return out
def resolve_day(day_arg:str, tz:str)->str:
    if day_arg: return day_arg
    from zoneinfo import ZoneInfo
    now=datetime.datetime.now(ZoneInfo(tz))
    return (now.date()+datetime.timedelta(days=1)).isoformat()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day",nargs="?")
    ap.add_argument("--csv",default=None)
    ap.add_argument("--cfg",default="config_pp_edge_v6.8.yaml")
    ap.add_argument("--out",default="alloc_summary.csv")
    ap.add_argument("--tz",default="America/Los_Angeles")
    a=ap.parse_args()
    day=resolve_day(a.day,a.tz)
    cfg=_load_yaml(Path(a.cfg))
    rows=_read_edges(Path(a.csv or f"edge_sheet_{day}.csv"))
    out_rows=allocate(rows,cfg)
    fields=["player","game_id","tier","slip_type","stake"]
    with Path(a.out).open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields)
        w.writeheader()
        for r in out_rows: w.writerow({k:r.get(k) for k in fields})
    print("OK" if any(float(r.get("stake") or 0)>0 for r in out_rows) else "WARN")
if __name__=="__main__": main()
