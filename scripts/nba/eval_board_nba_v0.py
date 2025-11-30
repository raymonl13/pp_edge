#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def _log(msg: str) -> None:
    print(f"[eval_board_nba_v0] {msg}")


def _load_joined(day: str, runs_root: Path) -> pd.DataFrame:
    runs_dir = runs_root / day
    joined_path = runs_dir / f"joined_with_phit_{day}.csv"
    if not joined_path.exists():
        raise SystemExit(f"joined_with_phit file not found: {joined_path}")
    return pd.read_csv(joined_path)


def _load_labels(day: str, labels_root: Path) -> pd.DataFrame:
    labels_path = labels_root / f"points_train_{day}.csv"
    if not labels_path.exists():
        raise SystemExit(f"labels file not found: {labels_path}")
    return pd.read_csv(labels_path)


def eval_day(day: str, runs_root: Path, labels_root: Path, market: str) -> None:
    _log(f"DAY={day}")
    joined = _load_joined(day, runs_root)
    labels = _load_labels(day, labels_root)

    # Normalize player name
    if "player_name" in joined.columns and "player" not in joined.columns:
        joined = joined.rename(columns={"player_name": "player"})
    if "player" not in joined.columns:
        raise SystemExit("Joined file has no 'player' or 'player_name' column")

    # Market column
    if "market" in joined.columns:
        mcol = "market"
    elif "market_norm" in joined.columns:
        mcol = "market_norm"
    else:
        raise SystemExit("Joined file has no 'market' or 'market_norm' column")

    joined[mcol] = joined[mcol].astype(str)
    joined_market = joined[joined[mcol].str.lower() == market.lower()].copy()
    total_points_rows = len(joined_market)
    _log(f"joined rows (market={market}): {total_points_rows}")

    # Labels sanity
    expected_label_cols = {"player", "team", "line", "actual_points", "hit"}
    missing = expected_label_cols - set(labels.columns)
    if missing:
        raise SystemExit(f"Labels file missing columns: {missing}")

    # Align types
    joined_market["line"] = joined_market["line"].astype(float)
    labels["line"] = labels["line"].astype(float)

    # Subset joined columns
    keep_cols = ["player", "team", mcol, "line", "p_hit", "edge_pp", "odds_type", "game_id"]
    keep_cols = [c for c in keep_cols if c in joined_market.columns]
    joined_sub = joined_market[keep_cols].copy()
    joined_sub = joined_sub.rename(columns={mcol: "market"})

    # Merge with labels on (player, team, line)
    merged = joined_sub.merge(
        labels[["player", "team", "line", "actual_points", "hit"]],
        on=["player", "team", "line"],
        how="inner",
        suffixes=("", "_label"),
    )

    matched_rows = len(merged)
    _log(f"matched rows (market={market}): {matched_rows}")
    if total_points_rows > 0:
        match_rate = matched_rows / total_points_rows
        _log(f"match_rate (market={market}) = {match_rate:.3f}")
    else:
        _log("no joined rows for this market; nothing to evaluate")
        return

    if matched_rows == 0:
        _log("No overlapping rows between joined and labels; nothing to evaluate")
        return

    merged["hit"] = merged["hit"].astype(float)
    merged["p_hit"] = merged["p_hit"].astype(float)
    merged["brier"] = (merged["p_hit"] - merged["hit"]) ** 2
    brier = float(merged["brier"].mean())
    _log(f"Brier score (lower is better): {brier:.4f}")

    # Bin by p_hit
    bins = [0.0, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 1.0]
    merged["p_bin"] = pd.cut(merged["p_hit"], bins=bins, include_lowest=True)

    calib = (
        merged
        .groupby("p_bin", observed=False)
        .agg(
            n=("hit", "size"),
            avg_p_hit=("p_hit", "mean"),
            actual_hit_rate=("hit", "mean"),
            avg_edge_pp=("edge_pp", "mean"),
        )
        .reset_index()
    )

    print(f"\n=== Full-board calibration (market={market}) for {day} ===")
    print(calib.to_string(index=False))

    # Optional: by odds_type
    if "odds_type" in merged.columns:
        calib_odds = (
            merged
            .groupby(["odds_type", "p_bin"], observed=False)
            .agg(
                n=("hit", "size"),
                avg_p_hit=("p_hit", "mean"),
                actual_hit_rate=("hit", "mean"),
                avg_edge_pp=("edge_pp", "mean"),
            )
            .reset_index()
        )
        print(f"\n=== Calibration by odds_type & p_bin for {day} ===")
        print(calib_odds.to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Full-board calibration for NBA Points props (p_hit vs actual hit rate)."
    )
    ap.add_argument("--day", required=True, help="Day in YYYY-MM-DD format, e.g. 2025-11-21")
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
        "--market",
        default="points",
        help="Market to evaluate (default: points)",
    )
    args = ap.parse_args()

    eval_day(args.day, Path(args.runs_root), Path(args.labels_root), args.market)


if __name__ == "__main__":
    main()
