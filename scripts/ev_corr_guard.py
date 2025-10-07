#!/usr/bin/env python3
import os, csv, json
from pathlib import Path

def read_csv(path):
    try:
        with open(path, newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []

def load_policy():
    try:
        import yaml
        p=Path("ci/ev_policy.yaml")
        if not p.exists(): raise FileNotFoundError
        return yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {
            "version":"1.0",
            "min_ev_threshold":0.02,
            "max_pairwise_corr":0.35,
            "slip_types":{
                "Power4":{"enabled":True,"min_ev_threshold":0.02},
                "Power6":{"enabled":True,"min_ev_threshold":0.025},
                "Flex6":{"enabled":True,"min_ev_threshold":0.015}
            },
            "corr_proxy_fields":["game_id","matchup","team","opp","market"]
        }

def to_float(x):
    try: return float(x)
    except Exception: return None

def top_legs(rows, slip_type, n_req):
    legs=[]
    for r in rows:
        st=(r.get("slip_type") or "").strip()
        if st!=slip_type: continue
        ph = r.get("pred_hit_prob") or r.get("p_hit") or r.get("prob")
        phf = to_float(ph)
        if phf is None: continue
        legs.append(r | {"__p":phf})
    legs.sort(key=lambda r: r["__p"], reverse=True)
    return legs[:n_req]

def pair_proxy(a,b,fields):
    score=0.0
    for f in fields:
        va=a.get(f); vb=b.get(f)
        if va is None or vb is None or str(va)=="" or str(vb)=="": 
            continue
        if va==vb:
            if f in ("game_id","matchup"):
                score=max(score, 1.0)
            elif f in ("team","opp"):
                score=max(score, 0.7)
            elif f in ("market",):
                score=max(score, 0.5)
            else:
                score=max(score, 0.3)
    return score

def analyze(rows, pol, day):
    fields = pol.get("corr_proxy_fields") or ["game_id","matchup","team","opp","market"]
    n_req_map={"Power4":4,"Power6":6,"Flex6":6}
    mx = float(pol.get("max_pairwise_corr") or 0.35)
    summary=[]; details={}
    for st in ("Power4","Power6","Flex6"):
        if not (pol.get("slip_types",{}).get(st,{}).get("enabled", True)):
            continue
        n_req=n_req_map.get(st,4)
        legs=top_legs(rows, st, n_req)
        if len(legs)<n_req:
            summary.append({"slip_type":st,"status":"INSUFFICIENT_LEGS","n":len(legs),"max_proxy":None,"threshold":mx})
            continue
        max_proxy=0.0
        flagged=[]
        for i in range(len(legs)):
            for j in range(i+1, len(legs)):
                s=pair_proxy(legs[i], legs[j], fields)
                if s>max_proxy: max_proxy=s
                if s>=mx:
                    ai = legs[i].get("player") or legs[i].get("name") or f"leg{i}"
                    aj = legs[j].get("player") or legs[j].get("name") or f"leg{j}"
                    flagged.append({"i":i,"j":j,"players":[ai,aj],"proxy":round(s,3)})
        status = "HIGH_CORR" if max_proxy>=mx else "OK"
        summary.append({"slip_type":st,"status":status,"n":len(legs),"max_proxy":round(max_proxy,3),"threshold":mx})
        details[st]={"fields_used":fields,"pairs_flagged":flagged}
    out={"version":"1.0","day":day,"summary":summary,"details":details}
    return out

def main():
    day=os.environ.get("DAY","")
    edge=f"edge_sheet_{day}.csv" if day else None
    rows=read_csv(edge) if edge and Path(edge).exists() else []
    pol=load_policy()
    out=analyze(rows, pol, day)
    Path("ev_correlation.json").write_text(json.dumps(out,indent=2))
    msg=" ".join(f"{s['slip_type']}={s['status']}@{s.get('max_proxy')}" for s in out["summary"])
    print(f"[ev-corr] {msg}")
if __name__=="__main__":
    main()
