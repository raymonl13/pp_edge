#!/usr/bin/env python3
import csv,json,argparse,sys,datetime
from collections import Counter,defaultdict
from pathlib import Path
from typing import Dict,List,Any
QA_RULES_VERSION="4.1.0"
REQUIRED_COLS=("player","game_id","p_hit","edge_pp","tier","slip_type")
def load_edge_sheet(path:Path)->List[Dict[str,Any]]:
    rows=[]
    with path.open(newline="") as fh:
        rdr=csv.DictReader(fh)
        fn=rdr.fieldnames or []
        missing=[c for c in REQUIRED_COLS if c not in fn]
        if missing: raise SystemExit(f"missing required columns: {missing}")
        for r in rdr: rows.append(r)
    return rows
def _to_float(v)->float:
    try: return float(v)
    except Exception: return float("nan")
def run_qa(rows:List[Dict[str,Any]],cfg:Dict[str,Any])->Dict[str,Any]:
    qa_cfg=cfg.get("qa",{}) or {}
    tiers=(cfg.get("tiers",{}) or {}).get("kelly_multiplier",{}) or {}
    valid_tiers=set(tiers.keys()) if tiers else {"Demon","Goblin","Standard"}
    min_rows=int(qa_cfg.get("min_rows",100))
    max_demon_per_slip=int(qa_cfg.get("max_demon_per_slip",1))
    slip_leg_sizes:Dict[str,int]=qa_cfg.get("slip_type_legs",{}) or {}
    issues=[]; hard=False; warn=False
    n=len(rows)
    if n<min_rows: issues.append({"severity":"FAIL","msg":f"rows_below_min:{n}<{min_rows}"}); hard=True
    empty_player=sum(1 for r in rows if not (r.get("player","").strip()))
    empty_gid=sum(1 for r in rows if not (r.get("game_id","").strip()))
    if empty_player: issues.append({"severity":"FAIL","msg":f"empty_player_rows:{empty_player}"}); hard=True
    if empty_gid: issues.append({"severity":"FAIL","msg":f"empty_game_id_rows:{empty_gid}"}); hard=True
    bad_tier=[r for r in rows if r.get("tier") not in valid_tiers]
    if bad_tier: issues.append({"severity":"FAIL","msg":f"invalid_tier_rows:{len(bad_tier)}"}); hard=True
    bad_phit=sum(1 for r in rows if (_to_float(r.get("p_hit"))==_to_float(r.get("p_hit"))) and not (0.0<=_to_float(r.get("p_hit"))<=1.0))
    if bad_phit: issues.append({"severity":"FAIL","msg":f"p_hit_out_of_range_rows:{bad_phit}"}); hard=True
    by_type=defaultdict(list)
    for r in rows: by_type[r.get("slip_type","")].append(r)
    for s_type,bucket in by_type.items():
        demons=sum(1 for r in bucket if r.get("tier")=="Demon")
        share=demons/max(1,len(bucket))
        leg_sz=slip_leg_sizes.get(s_type)
        if leg_sz and leg_sz>0:
            allowed_share=max_demon_per_slip/float(leg_sz)
            if share>allowed_share+1e-9: issues.append({"severity":"FAIL","msg":f"demon_share_exceeds_cap:{s_type}:{share:.2f}>{allowed_share:.2f}"}); hard=True
        else:
            if share>0.40: issues.append({"severity":"FAIL","msg":f"demon_share_excess:{s_type}:{share:.2f}"}); hard=True
            elif share>0.33: issues.append({"severity":"WARN","msg":f"demon_share_high:{s_type}:{share:.2f}"}); warn=True
    has_league=bool(rows and ("league" in rows[0].keys()))
    league_counts=Counter(r.get("league","UNKNOWN") for r in rows) if has_league else {}
    if has_league and league_counts:
        real={k:v for k,v in league_counts.items() if k not in ("","UNKNOWN",None)}
        if len(real)>1:
            top=max(real.values())/max(1,n)
            if top>0.90: issues.append({"severity":"WARN","msg":f"single_league_dominant:{top:.2f}"}); warn=True
        if len(real)>4 and sum(1 for v in real.values() if v<10)>2:
            issues.append({"severity":"WARN","msg":"multi_league_suspicious_mix"}); warn=True
    tier_counts=Counter(r.get("tier") for r in rows if r.get("tier") in valid_tiers)
    nan_phit=sum(1 for r in rows if _to_float(r.get("p_hit"))!=_to_float(r.get("p_hit")))
    if nan_phit: issues.append({"severity":"WARN","msg":f"nan_p_hit_rows:{nan_phit}"}); warn=True
    state="FAIL" if hard else ("WARN" if warn else "OK")
    return {"state":state,"rules_version":QA_RULES_VERSION,"counts":{"rows":n,"empty_player":empty_player,"empty_game_id":empty_gid,"invalid_tier":len(bad_tier),"tier_distribution":dict(tier_counts),"league_distribution":dict(league_counts) if has_league else {}},"issues":issues[:200]}
def _load_yaml(path:Path)->Dict[str,Any]:
    import yaml
    return yaml.safe_load(path.read_text()) or {}
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
    ap.add_argument("--tz",default="America/Los_Angeles")
    a=ap.parse_args()
    day=resolve_day(a.day,a.tz)
    rows=load_edge_sheet(Path(a.csv or f"edge_sheet_{day}.csv"))
    rep=run_qa(rows,_load_yaml(Path(a.cfg)))
    Path("qa_report.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    with Path("qa_report.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=["severity","msg"])
        w.writeheader()
        for i in rep.get("issues",[]): w.writerow(i)
    print(rep.get("state","UNKNOWN")); sys.exit(0)
if __name__=="__main__": main()
