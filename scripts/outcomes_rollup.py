#!/usr/bin/env python3
import argparse, json, pathlib, re
from typing import Optional, Tuple
import numpy as np
import pandas as pd

DAY_RX = re.compile(r"(\d{4}-\d{2}-\d{2})")

def _coerce_day_from_name(p: pathlib.Path) -> Optional[str]:
    m = DAY_RX.search(p.stem)
    return m.group(1) if m else None

def _load_realized_by_day(realized_glob: str) -> dict:
    out = {}
    for p in sorted(pathlib.Path(".").glob(realized_glob)):
        day = _coerce_day_from_name(p)
        if not day:
            continue
        df = pd.read_csv(p)
        df = df.rename(columns={"result":"outcome","win":"outcome"})
        df["outcome"] = df["outcome"].astype(int)
        df["stake"] = df["stake"].astype(float)
        df["payout"] = df["payout"].astype(float)
        out[day] = df
    return out

def _load_probs_from_edge_sheet(day: str) -> Optional[pd.DataFrame]:
    p = pathlib.Path(f"edge_sheet_{day}.csv")
    if not p.exists():
        return None
    df = pd.read_csv(p)
    for c in ("p_hit","p","prob","prob_win"):
        if c in df.columns:
            df = df.rename(columns={c:"p"})
            break
    if "p" not in df.columns:
        return None
    if "leg_id" not in df.columns:
        key_cols = [c for c in ("player","stat","line") if c in df.columns]
        if key_cols:
            df["leg_id"] = df[key_cols].astype(str).agg("|".join, axis=1)
        else:
            return None
    return df[["leg_id","p"]].drop_duplicates()

def _brier_and_logloss(y: pd.Series, p: pd.Series) -> Tuple[Optional[float], Optional[float]]:
    if len(y) == 0 or len(p) == 0:
        return None, None
    p = p.clip(1e-12, 1-1e-12)
    brier = float(np.mean((p - y) ** 2))
    logloss = float(-np.mean(y*np.log(p) + (1-y)*np.log(1-p)))
    return brier, logloss

def build_rollup(outcomes_glob: str, realized_glob: str, out_csv: str, out_json: str):
    realized_by_day = _load_realized_by_day(realized_glob)
    daily = []
    for day, df_r in sorted(realized_by_day.items()):
        staked = df_r["stake"].sum()
        payout = df_r["payout"].sum()
        roi = None if staked == 0 else float((payout - staked) / staked)
        probs = _load_probs_from_edge_sheet(day)
        brier = None
        logloss = None
        if probs is not None and "leg_id" in df_r.columns:
            j = pd.merge(df_r[["leg_id","outcome"]], probs, on="leg_id", how="inner")
            if not j.empty:
                brier, logloss = _brier_and_logloss(j["outcome"].astype(float), j["p"].astype(float))
        daily.append({
            "date": day,
            "total_legs": int(len(df_r)),
            "total_staked": float(staked),
            "total_payout": float(payout),
            "roi": None if roi is None else float(round(roi, 6)),
            "brier": None if brier is None else float(round(brier, 6)),
            "logloss": None if logloss is None else float(round(logloss, 6)),
        })
    pathlib.Path("outcomes").mkdir(parents=True, exist_ok=True)
    if not daily:
        pd.DataFrame(daily).to_csv(out_csv, index=False)
        pathlib.Path(out_json).write_text(json.dumps({"days": 0, "trailing": {}, "latest": {}}, indent=2))
        print("[rollup] days=0 roi=None brier=None")
        return 0, None, None
    df = pd.DataFrame(daily).sort_values("date")
    df.to_csv(out_csv, index=False)
    def trailing(k: int) -> dict:
        t = df.tail(k)
        st = t["total_staked"].sum()
        py = t["total_payout"].sum()
        troi = None if st == 0 else (py - st) / st
        tbrier = None if t["brier"].dropna().empty else float(t["brier"].mean())
        tlog = None if t["logloss"].dropna().empty else float(t["logloss"].mean())
        return {"days": int(len(t)), "roi": None if troi is None else float(round(troi, 6)), "brier": tbrier, "logloss": tlog}
    t7 = trailing(7)
    t30 = trailing(30)
    latest = df.iloc[-1].to_dict()
    pathlib.Path(out_json).write_text(json.dumps({"days": int(len(df)), "trailing": {"d7": t7, "d30": t30}, "latest": latest}, indent=2))
    rep_roi = t30["roi"] if t30["roi"] is not None else (t7["roi"] if t7["roi"] is not None else latest.get("roi"))
    rep_brier = t30["brier"] if t30["brier"] is not None else (t7["brier"] if t7["brier"] is not None else latest.get("brier"))
    print(f"[rollup] days={len(df)} roi={rep_roi} brier={rep_brier}")
    return len(df), rep_roi, rep_brier

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outcomes_glob", default="outcomes/outcomes_*.jsonl")
    ap.add_argument("--realized_glob", default="realized/realized_*.csv")
    ap.add_argument("--out_csv", default="outcomes/outcomes_rollup.csv")
    ap.add_argument("--out_json", default="outcomes/outcomes_rollup.json")
    args = ap.parse_args()
    build_rollup(args.outcomes_glob, args.realized_glob, args.out_csv, args.out_json)

if __name__ == "__main__":
    main()
