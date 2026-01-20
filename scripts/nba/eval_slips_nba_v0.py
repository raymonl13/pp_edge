#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd


def _log(msg: str) -> None:
    print(f"[eval_slips_nba_v0] {msg}")


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


def evaluate_day(day: str, runs_root: Path, labels_root: Path, slips_file: Path | None = None) -> None:
    runs_dir = runs_root / day

    slips_path = slips_file if slips_file is not None else runs_dir / "slips_nba_v0.csv"
    preds_path = runs_dir / f"joined_with_phit_{day}.csv"
    labels_path = labels_root / f"points_train_{day}.csv"

    if not slips_path.exists():
        raise SystemExit(f"Slips file not found: {slips_path}")
    if not preds_path.exists():
        raise SystemExit(f"Predictions file not found: {preds_path}")
    if not labels_path.exists():
        raise SystemExit(f"Labels file not found: {labels_path}")

    _log(f"DAY={day}")
    _log(f"slips={slips_path}")
    _log(f"preds={preds_path}")
    _log(f"labels={labels_path}")

    slips = pd.read_csv(slips_path)
    preds = pd.read_csv(preds_path)
    labels = pd.read_csv(labels_path)

    legs = _expand_slip_legs(slips)
    _log(f"expanded legs rows={len(legs)}")

    # Normalize player name in preds if needed
    if "player_name" in preds.columns and "player" not in preds.columns:
        preds = preds.rename(columns={"player_name": "player"})

    # Determine market column
    if "market" in preds.columns:
        mcol = "market"
    elif "market_norm" in preds.columns:
        mcol = "market_norm"
    else:
        raise SystemExit("Predictions file has no 'market' or 'market_norm' column")

    preds_sub = preds[["player", mcol, "line", "p_hit", "edge_pp", "team"]].rename(columns={mcol: "market"})

    legs = legs.merge(
        preds_sub,
        on=["player", "market", "line"],
        how="left",
    )
    _log(f"after merge with preds, legs rows={len(legs)}, with p_hit non-null={legs['p_hit'].notna().sum()}")

    # Join labels on (player, team, line)
    labels_sub = labels[["player", "team", "line", "actual_points", "hit"]]
    legs = legs.merge(
        labels_sub,
        on=["player", "team", "line"],
        how="left",
    )
    _log(
        f"after merge with labels, legs rows={len(legs)}, "
        f"with hit non-null={legs['hit'].notna().sum()}"
    )

    if legs["hit"].notna().sum() == 0:
        _log("No labeled legs for this day; nothing to evaluate.")
        print("=== Slip legs (no labels available) ===")
        print(
            legs[
                ["slip_id", "slip_type", "player", "team", "market", "line", "p_hit", "edge_pp", "actual_points", "hit"]
            ].to_string(index=False)
        )
        return

    print("=== Slip legs with predictions and outcomes ===")
    print(
        legs[
            ["slip_id", "slip_type", "player", "team", "market", "line", "p_hit", "edge_pp", "actual_points", "hit"]
        ].to_string(index=False)
    )

    # Slip-level outcome: 1 if all labeled legs hit; 0 if any labeled leg missed; None if any leg unlabeled
    def slip_outcome(hit_series: pd.Series):
        if hit_series.isna().any():
            return None
        return int((hit_series == 1).all())

    slip_results = legs.groupby("slip_id")["hit"].apply(slip_outcome).reset_index()
    slip_results.columns = ["slip_id", "slip_all_hit"]

    print("\n=== Slip-level outcomes (1=all labeled hit, 0=any labeled miss, None=some unlabeled) ===")
    print(slip_results.to_string(index=False))

    # Calibration by p_hit bin (only for legs with labels)
    labeled_legs = legs[legs["hit"].notna()].copy()
    bins = [0.0, 0.45, 0.5, 0.55, 0.6, 1.0]
    labeled_legs["p_bin"] = pd.cut(labeled_legs["p_hit"], bins=bins, include_lowest=True)

    calib = (
        labeled_legs
        .groupby("p_bin", observed=False)
        .agg(
            n=("hit", "size"),
            avg_p_hit=("p_hit", "mean"),
            actual_hit_rate=("hit", "mean"),
            avg_edge_pp=("edge_pp", "mean"),
        )
        .reset_index()
    )

    print("\n=== Calibration by p_hit bin ===")
    print(calib.to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Evaluate NBA v0 slips for a given day (leg-level outcomes & calibration)."
    )
    ap.add_argument("--day", required=True, help="Day in YYYY-MM-DD format, e.g. 2025-11-19")
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
        "--slips-file",
        default=None,
        help="Optional explicit path to slips CSV. If not set, uses runs_root/<DAY>/slips_nba_v0.csv",
    )
    args = ap.parse_args()

    day = args.day
    runs_root = Path(args.runs_root)
    labels_root = Path(args.labels_root)
    slips_file = Path(args.slips_file) if args.slips_file else None

    evaluate_day(day, runs_root, labels_root, slips_file)


if __name__ == "__main__":
    main()
