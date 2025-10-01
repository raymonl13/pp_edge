#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, json, hashlib
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import yaml

def _iso_day(day: str | None) -> str:
    if day: return day
    return (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

def _load_board(day_iso: str) -> List[Dict[str, Any]]:
    p = Path(f"data/pricefix_{day_iso}.json")
    if not p.exists(): return []
    with p.open() as f:
        data = json.load(f)
    return data if isinstance(data, list) else []

def _load_cfg(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists(): return {}
    with p.open() as f:
        d = yaml.safe_load(f) or {}
    return d if isinstance(d, dict) else {}

def _stable_game_id(r: Dict[str, Any], day_iso: str) -> str:
    raw = f"{r.get('player','?')}|{r.get('team','?')}|{r.get('stat','?')}|{r.get('line','?')}|{day_iso}"
    h = hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]
    return f"pf-{h}"

def _payout_scalar(entry: Any) -> float:
    if isinstance(entry, (int,float,np.floating)): return float(entry)
    if isinstance(entry, dict):
        vals = [float(v) for v in entry.values() if isinstance(v,(int,float,np.floating))]
        if vals: return float(max(vals))
    return 1.0

def _choose_tier(edge_pp: float, tiers_cfg: Dict[str, Any] | None) -> str:
    tiers_cfg = tiers_cfg or {}
    pairs = []
    for k,v in tiers_cfg.items():
        try: pairs.append((str(k), float((v or {}).get('min_edge', -1.0))))
        except Exception: pass
    if not pairs: pairs = [('Demon',0.12),('Goblin',0.06),('Standard',-1.0)]
    pairs.sort(key=lambda x: x[1], reverse=True)
    for name,thr in pairs:
        if edge_pp >= thr: return name
    return pairs[-1][0]

def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1-1e-6)
    return np.log(p/(1-p))

def _inv_logit(z: np.ndarray) -> np.ndarray:
    return 1.0/(1.0+np.exp(-z))

def _apply_calibration(p: np.ndarray, cal_cfg: Dict[str, Any] | None) -> tuple[np.ndarray,str]:
    if not cal_cfg: return p, "SKIP"
    method = str(cal_cfg.get("method","")).lower()
    if method in ("","none","skip","false","0"): return p,"SKIP"
    try:
        if method=="platt":
            A=float(cal_cfg.get("A",cal_cfg.get("a",1.0))); B=float(cal_cfg.get("B",cal_cfg.get("b",0.0)))
            return _inv_logit(A*_logit(p)+B), "APPLIED"
        if method=="isotonic":
            pairs=cal_cfg.get("pairs") or []
            xs=np.array([float(a) for a,_ in pairs],dtype=float)
            ys=np.array([float(b) for _,b in pairs],dtype=float)
            order=np.argsort(xs)
            return np.interp(p, xs[order], ys[order]), "APPLIED"
        return p,"UNKNOWN_METHOD"
    except Exception:
        return p,"ERROR"

def _fallback_prob(rows: List[Dict[str,Any]], fb_cfg: Dict[str,Any] | None) -> np.ndarray:
    fb_cfg = fb_cfg or {}
    base = float(fb_cfg.get('p_hit_default', 0.52))
    stat_map = fb_cfg.get('stat_bias') or {}
    out=[]
    for r in rows:
        p = float(stat_map.get(str(r.get('stat','')).upper(), base))
        try:
            line_val=float(r.get('line',0.0))
            p = p - min(0.05, abs(line_val)*0.001)
        except Exception:
            pass
        out.append(min(0.95,max(0.05,p)))
    return np.asarray(out,dtype=float)

def score_rows(rows: List[Dict[str,Any]], cfg: Dict[str,Any], day_iso: str):
    payouts = cfg.get('payouts') or {'Power2':3.0,'Power3':5.0,'Power4':10.0,'Power6':25.0,'Flex4':{'4':1.5,'3':0.5},'Flex5':{'5':10.0,'4':2.0}}
    slip_types = list(payouts.keys())
    model_cfg = cfg.get('model') or {}
    art_path = (model_cfg.get('artifacts') or {}).get('model_path') or 'model_assets/model_v1.pkl'
    model_state='MISSING'
    try:
        mp=Path(art_path)
        if mp.exists():
            from code_utils_model_v1 import predict_hit_prob
            feat_df=pd.DataFrame(rows)
            p_raw=np.asarray(predict_hit_prob(feat_df, model_path=mp),dtype=float)
            p_raw=np.clip(p_raw,1e-6,1-1e-6)
            model_state='OK'
        else:
            p_raw=_fallback_prob(rows, model_cfg.get('fallback')); model_state='MISSING'
    except Exception:
        p_raw=_fallback_prob(rows, model_cfg.get('fallback')); model_state='ERROR'
    p_cal, cal_state = _apply_calibration(p_raw, model_cfg.get('calibration'))
    out=[]
    for i,r in enumerate(rows):
        gid=_stable_game_id(r, day_iso)
        for s_type in slip_types:
            pay=_payout_scalar(payouts[s_type])
            p_hit=float(p_cal[i])
            edge=round(p_hit*pay-1.0,4)
            tier=_choose_tier(edge, cfg.get('tiers'))
            out.append({'player':r.get('player'),'game_id':gid,'p_hit':round(p_hit,4),'edge_pp':edge,'tier':tier,'slip_type':s_type})
    df=pd.DataFrame(out, columns=['player','game_id','p_hit','edge_pp','tier','slip_type'])
    return df, model_state, cal_state

def _append_meta(model_state:str, cal_state:str, count:int, out_csv:Path) -> None:
    lines=[f"MODEL_STATE={model_state}", f"CAL_STATE={cal_state}", f"SCORED_ROWS={count}"]
    for ln in lines: print(ln)
    with open('run_meta.txt','a') as fh: fh.write('\n'.join(lines)+'\n')
    print(f"EDGE_SHEET={out_csv}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('day', nargs='?')
    ap.add_argument('--cfg', default='config_pp_edge_v6.8.yaml')
    args=ap.parse_args()
    day=_iso_day(args.day)
    rows=_load_board(day)
    cfg=_load_cfg(args.cfg)
    df, ms, cs = score_rows(rows, cfg, day)
    out=Path(f'edge_sheet_{day}.csv')
    df.to_csv(out, index=False)
    print(f'edge sheet written -> {out} rows:{len(df)}')
    _append_meta(ms, cs, len(df), out)

if __name__=='__main__':
    main()
