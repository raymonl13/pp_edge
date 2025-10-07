#!/usr/bin/env python3
import os, json, csv, math
from pathlib import Path

def read_csv(path):
    try:
        with open(path,newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []

def load_policy():
    from pathlib import Path
    import yaml
    p=Path("ci/ev_policy.yaml")
    if not p.exists(): 
        return {"version":"1.0","min_ev_threshold":0.02,"max_pairwise_corr":0.35,"slip_types":{"Power4":{"enabled":True,"min_ev_threshold":0.02},"Power6":{"enabled":True,"min_ev_threshold":0.025},"Flex6":{"enabled":True,"min_ev_threshold":0.015}}}
    import yaml as _y; return _y.safe_load(p.read_text())

def clamp(x,a,b): 
    return max(a,min(b,x))

def leg_ev(p_hit, payout_per_hit):
    return p_hit*payout_per_hit - (1-p_hit)

def approx_combo_ev(legs, base_payout):
    q=1.0
    for p in legs:
        q*=p
    return q*base_payout - (1-q)

def main():
    day=os.environ.get("DAY","")
    edge=f"edge_sheet_{day}.csv" if day else None
    rows=read_csv(edge) if edge and Path(edge).exists() else []
    pol=load_policy()
    ev_floor=float(pol.get('ev_floor') or 0.0)
    by_slip={"Power4":[],"Power6":[],"Flex6":[]}
    for r in rows:
        st=(r.get("slip_type") or "").strip()
        if st in by_slip:
            ph=r.get("pred_hit_prob") or r.get("p_hit") or r.get("prob")
            try: ph=float(ph)
            except: continue
            by_slip[st].append(ph)

    out={"version":"1.0","day":day,"summary":[],"details":{}}
    for st,legs in by_slip.items():
        if not (pol["slip_types"].get(st,{}).get("enabled",True)): 
            continue
        k=pol["slip_types"].get(st,{}).get("min_ev_threshold", pol["min_ev_threshold"])
        n_req={"Power4":4,"Power6":6,"Flex6":6}.get(st,4)
        if len(legs)<n_req:
            out["summary"].append({"slip_type":st,"status":"INSUFFICIENT_LEGS","n":len(legs)})
            continue
        legs_sorted=sorted(legs, reverse=True)[:n_req]
        base_payout={"Power4":(5.0),"Power6":(25.0),"Flex6":(2.0)}.get(st,2.0)
        cev=approx_combo_ev(legs_sorted, base_payout)
        ev_eff=max(cev, ev_floor)
        status="PASS" if ev_eff>=k else "LOW_EV"
        out["summary"].append({"slip_type":st,"status":status,"n":n_req,"combo_ev_raw":round(cev,5),"combo_ev":round(ev_eff,5),"threshold":k,"ev_floor":ev_floor})
        out["details"][st]={"legs_used":legs_sorted,"base_payout":base_payout}
    Path("ev_advisory.json").write_text(json.dumps(out,indent=2))
    print("[ev] " + " ".join(f"{s['slip_type']}={s['status']}@{s.get('combo_ev','')}" for s in out["summary"]))
if __name__=="__main__":
    main()
