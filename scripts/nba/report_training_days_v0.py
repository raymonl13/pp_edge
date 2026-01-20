#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


def _log(msg: str) -> None:
    print(f"[report_training_days_v0] {msg}")


def _infer_day_from_filename(path: Path) -> str:
    """
    Extract YYYY-MM-DD from filenames like points_train_YYYY-MM-DD.csv
    """
    name = path.name
    stem = name.replace("points_train_", "").replace(".csv", "")
    return stem


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Summarize per-day label coverage and unmatched counts for NBA training data."
    )
    ap.add_argument(
        "--daily-dir",
        default="data/nba/modeling/daily",
        help="Directory containing points_train_YYYY-MM-DD.csv (default: data/nba/modeling/daily)",
    )
    ap.add_argument(
        "--unmatched-dir",
        default="data/nba/modeling/unmatched",
        help="Directory containing unmatched_points_YYYY-MM-DD.csv (default: data/nba/modeling/unmatched)",
    )
    ap.add_argument(
        "--out",
        default="data/nba/modeling/training_days_report_v0.csv",
        help="CSV path to write the report (default: data/nba/modeling/training_days_report_v0.csv)",
    )
    args = ap.parse_args()

    daily_dir = Path(args.daily_dir)
    unmatched_dir = Path(args.unmatched_dir)
    out_path = Path(args.out)

    if not daily_dir.exists():
        raise SystemExit(f"daily-dir not found: {daily_dir}")

    daily_files: List[Path] = sorted(daily_dir.glob("points_train_*.csv"))
    if not daily_files:
        raise SystemExit(f"No points_train_*.csv files found in {daily_dir}")

    rows: List[Dict[str, Any]] = []

    for f in daily_files:
        day = _infer_day_from_filename(f)
        labels_df = pd.read_csv(f)
        n_labeled = len(labels_df)

        unmatched_path = unmatched_dir / f"unmatched_points_{day}.csv"
        if unmatched_path.exists():
            unmatched_df = pd.read_csv(unmatched_path)
            n_unmatched = len(unmatched_df)
        else:
            n_unmatched = 0

        total = n_labeled + n_unmatched
        match_rate = (n_labeled / total) if total > 0 else None

        rows.append(
            {
                "day": day,
                "n_labeled": n_labeled,
                "n_unmatched": n_unmatched,
                "total_points": total,
                "match_rate": match_rate,
            }
        )

    report_df = pd.DataFrame(rows).sort_values("day")
    _log("Per-day training coverage:")
    print(report_df.to_string(index=False))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(out_path, index=False)
    _log(f"wrote report to {out_path}")


if __name__ == "__main__":
    main()
