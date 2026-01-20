#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


def _log(msg: str) -> None:
    print(f"[report_slip_filter_metrics_v0] {msg}")


def _expand_slip_legs(slips: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    for _, row in slips.iterrows():
        slip_id = row["slip_id"]
        slip_type = row.get("slip_type")
        legs_str = str(row.get("legs", ""))
        for leg in legs_str.split("; "):
            if not leg.strip():
                continue
            try:
                player, market, line = leg.split("|")
                rows.append(
                    {
                        "slip_id": slip_id,
                        "slip_type": slip_type,
                        "player": player.strip(),
                        "market": market.strip(),
                        "line": float(line),
                    }
                )
            except ValueError:
                _log(f"WARNING: could not parse leg '{leg}' for slip_id={slip_id}")
    return pd.DataFrame(rows)


def metrics_for_day(day: str, runs_root: Path, labels_root: Path) -> Dict[str, Any]:
    runs_dir = runs_root / day
    slips_path = runs_dir / "slips_nba_v0.csv"
    slips_filt_path = runs_dir / "slips_nba_v0_filtered.csv"
    preds_path = runs_dir / f"joined_with_phit_{day}.csv"
    labels_path = labels_root / f"points_train_{day}.csv"

    if not slips_path.exists() or not preds_path.exists() or not labels_path.exists():
        return {
            "day": day,
            "n_slips_orig": None,
            "n_slips_filt": None,
            "n_legs_orig_labeled": None,
            "hit_rate_orig": None,
            "n_legs_filt_labeled": None,
            "hit_rate_filt": None,
        }

    slips = pd.read_csv(slips_path)
    slips_filt = pd.read_csv(slips_filt_path) if slips_filt_path.exists() else slips.head(0)
    preds = pd.read_csv(preds_path)
    labels = pd.read_csv(labels_path)

    # Normalize preds player / market
    if "player_name" in preds.columns and "player" not in preds.columns:
        preds = preds.rename(columns={"player_name": "player"})
    if "market" in preds.columns:
        mcol = "market"
    elif "market_norm" in preds.columns:
        mcol = "market_norm"
    else:
        return {
            "day": day,
            "n_slips_orig": len(slips),
            "n_slips_filt": len(slips_filt),
            "n_legs_orig_labeled": None,
            "hit_rate_orig": None,
            "n_legs_filt_labeled": None,
            "hit_rate_filt": None,
        }

    # For this report we only need player/market/line/team; p_hit/edge_pp are not required
    needed_cols = ["player", mcol, "line", "team"]
    missing = [c for c in needed_cols if c not in preds.columns]
    if missing:
        _log(f"WARNING: predictions for day={day} missing columns {missing}; skipping day")
        return {
            "day": day,
            "n_slips_orig": len(slips),
            "n_slips_filt": len(slips_filt),
            "n_legs_orig_labeled": None,
            "hit_rate_orig": None,
            "n_legs_filt_labeled": None,
            "hit_rate_filt": None,
        }
    preds_sub = preds[needed_cols].rename(columns={mcol: "market"})
    labels_sub = labels[["player", "team", "line", "actual_points", "hit"]]

    def leg_hit_rate(slips_df: pd.DataFrame) -> (int, float):
        if slips_df.empty:
            return 0, None
        legs = _expand_slip_legs(slips_df)
        if legs.empty:
            return 0, None
        legs = legs.merge(preds_sub, on=["player", "market", "line"], how="left")
        legs = legs.merge(labels_sub, on=["player", "team", "line"], how="left")
        labeled = legs[legs["hit"].notna()]
        if labeled.empty:
            return 0, None
        return len(labeled), float(labeled["hit"].mean())

    n_legs_orig_labeled, hit_rate_orig = leg_hit_rate(slips)
    n_legs_filt_labeled, hit_rate_filt = leg_hit_rate(slips_filt)

    return {
        "day": day,
        "n_slips_orig": len(slips),
        "n_slips_filt": len(slips_filt),
        "n_legs_orig_labeled": n_legs_orig_labeled,
        "hit_rate_orig": hit_rate_orig,
        "n_legs_filt_labeled": n_legs_filt_labeled,
        "hit_rate_filt": hit_rate_filt,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Summarize original vs filtered slips performance (leg-level labeled hit rate) per day."
    )
    ap.add_argument(
        "--runs-root",
        default="runs/nba",
        help="Root directory for run artifacts (default: runs/nba)",
    )
    ap.add_argument(
        "--labels-root",
        default="data/nba/modeling/daily",
        help="Root directory for per-day label files (default: data/nba/modeling/daily)",
    )
    ap.add_argument(
        "--out",
        default="data/nba/modeling/slip_filter_report_v0.csv",
        help="CSV path to write the report (default: data/nba/modeling/slip_filter_report_v0.csv)",
    )
    args = ap.parse_args()

    runs_root = Path(args.runs_root)
    labels_root = Path(args.labels_root)
    out_path = Path(args.out)

    # Infer days from labels (we only care about days with labels)
    label_days = sorted(p.stem.replace("points_train_", "") for p in labels_root.glob("points_train_*.csv"))
    rows: List[Dict[str, Any]] = []
    for day in label_days:
        rows.append(metrics_for_day(day, runs_root, labels_root))

    df = pd.DataFrame(rows).sort_values("day")
    _log("Slip filter metrics per day:")
    print(df.to_string(index=False))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    _log(f"wrote report to {out_path}")


if __name__ == "__main__":
    main()
