#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, json, hashlib, csv, math, bisect
from pathlib import Path
from typing import Dict, Any, List, Tuple

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
    try:
        import yaml
    except Exception:
        return {}
    with p.open() as f:
        d = (yaml.safe_load(f) or {})
    return d if isinstance(d, dict) else {}

def _stable_game_id(r: Dict[str, Any], day_iso: str) -> str:
    raw = f"{r.get('player','?')}|{r.get('team','?')}|{r.get('stat','?')}|{r.get('line','?')}|{day_iso}"
    h = hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]
    return f"pf-{h}"

def _payout_scalar(entry: Any) -> float:
    if isinstance(entry, (int, float)): return float(entry)
    if isinstance(entry, dict):
        vals = [float(v) for v in entry.values() if isinstance(v, (int, float))]
        if vals: return max(vals)
    return 1.0

def _choose_tier(edge_pp: float, tiers_cfg: Dict[str, Any] | None) -> str:
    tiers_cfg = tiers_cfg or {}
    pairs: List[Tuple[str,float]] = []
    for k, v in tiers_cfg.items():
        try: pairs.append((str(k), float((v or {}).get('min_edge', -1.0))))
        except Exception: pass
    if not pairs: pairs = [('Demon', 0.12), ('Goblin', 0.06), ('Standard', -1.0)]
    pairs.sort(key=lambda x: x[1], reverse=True)
    for name, thr in pairs:
        if edge_pp >= thr: return name
    return pairs[-1][0]

def _logit_scalar(p: float) -> float:
    p = min(max(p, 1e-6), 1-1e-6)
    return math.log(p/(1-p))

def _inv_logit_scalar(z: float) -> float:
    return 1.0/(1.0+math.exp(-z))

def _apply_calibration(p_list: List[float], cal_cfg: Dict[str, Any] | None) -> tuple[List[float], str]:
    if not cal_cfg: return p_list, "SKIP"
    method = str(cal_cfg.get("method","")).lower()
    if method in ("","none","skip","false","0"): return p_list, "SKIP"
    try:
        if method == "platt":
            A = float(cal_cfg.get("A", cal_cfg.get("a", 1.0)))
            B = float(cal_cfg.get("B", cal_cfg.get("b", 0.0)))
            return [ _inv_logit_scalar(A*_logit_scalar(p) + B) for p in p_list ], "APPLIED"
        if method == "isotonic":
            pairs = cal_cfg.get("pairs") or []
            xs = [float(a) for a,_ in pairs]
            ys = [float(b) for _,b in pairs]
            if len(xs) < 2: return p_list, "CONFIG_EMPTY"
            order = sorted(range(len(xs)), key=lambda i: xs[i])
            xs = [xs[i] for i in order]; ys = [ys[i] for i in order]
            def interp(x: float) -> float:
                if x <= xs[0]: return ys[0]
                if x >= xs[-1]: return ys[-1]
                j = bisect.bisect_left(xs, x)
                x0,x1 = xs[j-1], xs[j]; y0,y1 = ys[j-1], ys[j]
                if x1 == x0: return y0
                return y0 + (y1 - y0) * ((x - x0) / (x1 - x0))
            return [ interp(p) for p in p_list ], "APPLIED"
        return p_list, "UNKNOWN_METHOD"
    except Exception:
        return p_list, "ERROR"

def _fallback_prob(rows: List[Dict[str,Any]], fb_cfg: Dict[str,Any] | None) -> List[float]:
    fb_cfg = fb_cfg or {}
    base = float(fb_cfg.get("p_hit_default", 0.505))
    stat_map = fb_cfg.get("stat_bias") or {}
    out: List[float] = []
    for r in rows:
        p = float(stat_map.get(str(r.get("stat","")).upper(), base))
        try:
            line_val = float(r.get("line", 0.0))
            p = p - min(0.05, abs(line_val) * 0.001)
        except Exception:
            pass
        out.append(min(0.95, max(0.05, p)))
    return out

def score_rows(rows: List[Dict[str,Any]], cfg: Dict[str,Any], day_iso: str) -> tuple[List[Dict[str,Any]], str, str]:
    payouts = cfg.get("payouts") or {"Power2":3.0,"Power3":5.0,"Power4":10.0,"Power6":25.0,"Flex4":{"4":1.5,"3":0.5},"Flex5":{"5":10.0,"4":2.0}}
    slip_types = list(payouts.keys())
    model_cfg = cfg.get("model") or {}
    art_path = (model_cfg.get("artifacts") or {}).get("model_path") or "model_assets/model_v1.pkl"
    model_state = "MISSING"
    try:
        mp = Path(art_path)
        if mp.exists():
            from code_utils_model_v1 import predict_hit_prob
            try:
                import pandas as pd
                p_raw = predict_hit_prob(pd.DataFrame(rows), model_path=mp)
            except Exception:
                p_raw = predict_hit_prob(rows, model_path=mp)
            try:
                p_raw = [float(x) for x in list(p_raw)]
            except Exception:
                p_raw = _fallback_prob(rows, model_cfg.get("fallback"))
                model_state = "ERROR"
            else:
                p_raw = [min(1-1e-6, max(1e-6, x)) for x in p_raw]
                model_state = "OK"
        else:
            p_raw = _fallback_prob(rows, model_cfg.get("fallback"))
            model_state = "MISSING"
    except Exception:
        p_raw = _fallback_prob(rows, model_cfg.get("fallback"))
        model_state = "ERROR"
    p_cal, cal_state = _apply_calibration(p_raw, model_cfg.get("calibration"))
    out: List[Dict[str,Any]] = []
    for i, r in enumerate(rows):
        gid = _stable_game_id(r, day_iso)
        p_hit_i = float(p_cal[i])
        for s_type in slip_types:
            pay = _payout_scalar(payouts[s_type])
            edge = round(p_hit_i * pay - 1.0, 4)
            tier = _choose_tier(edge, cfg.get("tiers"))
            out.append({"player": r.get("player"), "game_id": gid, "p_hit": round(p_hit_i, 4), "edge_pp": edge, "tier": tier, "slip_type": s_type})
    return out, model_state, cal_state

def _append_meta(model_state: str, cal_state: str, count: int, out_csv: Path) -> None:
    lines = [
        f"MODEL_STATE={model_state}",
        f"CAL_STATE={cal_state}",
        f"SCORED_ROWS={count}",
        f"CSV_ROWS={count}"
    ]
    for ln in lines: print(ln)
    with open("run_meta.txt","a") as fh: fh.write("\n".join(lines) + "\n")
    print(f"EDGE_SHEET={out_csv}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("day", nargs="?")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args = ap.parse_args()
    day = _iso_day(args.day)
    rows = _load_board(day)
    cfg  = _load_cfg(args.cfg)
    recs, mstate, cstate = score_rows(rows, cfg, day)
    out = Path(f"edge_sheet_{day}.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["player","game_id","p_hit","edge_pp","tier","slip_type"])
        w.writeheader()
        for r in recs: w.writerow(r)
    print(f"edge sheet written -> {out} rows:{len(recs)}")
    _append_meta(mstate, cstate, len(recs), out)

if __name__ == "__main__":
    main()
