#!/usr/bin/env python3
"""
rank_nba_edges_v0.py

Rank NBA PrizePicks props for a given day based on p_hit from joined_with_phit_{DAY}.csv.

- Assumes `p_hit` is the stub probability that the player goes OVER the line.
- Computes a simple edge score: edge_over = p_hit - 0.5.
- Writes a ranked CSV of props with features_found=True, sorted by edge_over descending.

WARNING: This is v0.1, based on season aggregates and a crude logistic mapping.
"""

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if x == "":
            return default
        return float(x)
    except Exception:
        return default


def rank_edges(in_path: Path, out_path: Path, min_games: int = 5) -> None:
    if not in_path.exists():
        raise FileNotFoundError(f"Joined-with-p_hit file not found: {in_path}")

    with in_path.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        rows: List[Dict[str, Any]] = list(reader)

    ranked: List[Dict[str, Any]] = []
    for row in rows:
        features_found = str(row.get("features_found", "")).strip().lower() == "true"
        if not features_found:
            continue

        games = safe_float(row.get("games"), 0.0)
        if games < min_games:
            # Skip tiny sample sizes
            continue

        p_hit = safe_float(row.get("p_hit"), 0.5)
        edge_over = p_hit - 0.5

        # attach edge fields
        row["edge_over"] = edge_over
        ranked.append(row)

    # sort by edge_over descending
    ranked.sort(key=lambda r: r.get("edge_over", 0.0), reverse=True)

    # Choose a subset of columns to output (for readability)
    fieldnames = [
        "player_name",
        "team",
        "game_date",
        "game_id",
        "market",
        "line",
        "odds_type",
        "p_hit",
        "edge_over",
        "games",
        "minutesPg",
        "points",
        "totalRb",
        "assists",
        "per",
        "tsPercent",
        "usagePercent",
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in ranked:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank NBA PP props by p_hit edge for a given day.")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--in-path", help="Input joined_with_phit CSV (default: runs/nba/{DAY}/joined_with_phit_{DAY}.csv)")
    parser.add_argument("--out-path", help="Output ranked CSV (default: runs/nba/{DAY}/ranked_edges_{DAY}.csv)")
    parser.add_argument("--min-games", type=int, default=5, help="Minimum games to include a player (default: 5)")
    args = parser.parse_args()

    day = args.day
    in_path = Path(args.in_path) if args.in_path else Path("runs") / "nba" / day / f"joined_with_phit_{day}.csv"
    out_path = Path(args.out_path) if args.out_path else Path("runs") / "nba" / day / f"ranked_edges_{day}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[rank_nba_edges_v0] day={day}")
    print(f"[rank_nba_edges_v0] in_path={in_path}")
    print(f"[rank_nba_edges_v0] out_path={out_path}")

    rank_edges(in_path, out_path, min_games=args.min_games)

    print(f"[rank_nba_edges_v0] wrote {out_path}")


if __name__ == "__main__":
    main()
