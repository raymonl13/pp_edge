#!/usr/bin/env python3
"""
add_p_hit_v0.py

Compute a stub p_hit for each NBA PrizePicks prop using real season features
from joined_{DAY}.csv (output of join_nba_season_v0.py).

This is a v0.1 structural model:

- Uses season totals per game (points, rebounds, assists).
- Compares per-game stat to the PrizePicks line for that market.
- Uses a simple logistic transform: p_hit = 1 / (1 + exp(-(stat_ppg - line) / scale)).
- Clamps p_hit to [0.01, 0.99].

WARNING: This is NOT a calibrated model; it's a monotone stub to make the lane real.
"""

import argparse
import csv
import math
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


def compute_stat_ppg(row: Dict[str, Any]) -> float:
    games = safe_float(row.get("games"), 0.0)
    if games <= 0:
        return 0.0

    pts = safe_float(row.get("points"), 0.0)
    rebs = safe_float(row.get("totalRb"), 0.0)
    asts = safe_float(row.get("assists"), 0.0)
    stl = safe_float(row.get("steals"), 0.0)
    blk = safe_float(row.get("blocks"), 0.0)

    market = (row.get("market") or "").lower()

    # Per-game stats
    ppg = pts / games
    rpg = rebs / games
    apg = asts / games

    # Map market to a proxy per-game stat
    if market == "points":
        return ppg
    if market.startswith("reb"):
        return rpg
    if "assist" in market:
        return apg
    if "pts+rebs+asts" in market or market == "pra":
        return (pts + rebs + asts) / games
    if "pts+rebs" in market:
        return (pts + rebs) / games
    if "fantasy score" in market:
        # very crude fantasy score proxy
        return (pts + 1.2 * rebs + 1.5 * asts + 3 * stl + 3 * blk) / games
    if "3-pt" in market or "3 pt" in market or "3pt" in market or "threes" in market:
        # No 3PM column, so fall back to ppg for now
        return ppg

    # Fallback: ppg
    return ppg


def logistic_p_hit(stat_ppg: float, line: float, market: str) -> float:
    delta = stat_ppg - line

    # Different scales for different stats
    market = market.lower()
    if market == "points" or "pts+rebs+asts" in market or "pra" in market:
        scale = 2.0
    elif "assist" in market or market.startswith("reb"):
        scale = 1.5
    else:
        scale = 2.0

    z = delta / scale
    p = 1.0 / (1.0 + math.exp(-z))
    # Clamp to avoid 0/1 extremes
    return max(0.01, min(0.99, p))


def add_p_hit(in_path: Path, out_path: Path) -> None:
    if not in_path.exists():
        raise FileNotFoundError(f"Joined file not found: {in_path}")

    with in_path.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        rows: List[Dict[str, Any]] = list(reader)

    out_fieldnames = list(reader.fieldnames or [])
    # Append if not present
    for extra in ["p_hit", "phit_source", "stat_ppg"]:
        if extra not in out_fieldnames:
            out_fieldnames.append(extra)

    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
        writer.writeheader()

        for row in rows:
            features_found = str(row.get("features_found", "")).strip().lower() == "true"
            market = (row.get("market") or "").lower()
            line = safe_float(row.get("line"), 0.0)

            if not features_found:
                row["stat_ppg"] = ""
                row["p_hit"] = 0.5
                row["phit_source"] = "nba_season_v0_missing_features"
            else:
                stat_ppg = compute_stat_ppg(row)
                row["stat_ppg"] = stat_ppg
                row["p_hit"] = logistic_p_hit(stat_ppg, line, market)
                row["phit_source"] = "nba_season_v0"

            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Add p_hit stub to joined NBA board using season features")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--in-path", help="Input joined CSV (default: runs/nba/{DAY}/joined_{DAY}.csv)")
    parser.add_argument("--out-path", help="Output CSV (default: runs/nba/{DAY}/joined_with_phit_{DAY}.csv)")
    args = parser.parse_args()

    day = args.day
    in_path = Path(args.in_path) if args.in_path else Path("runs") / "nba" / day / f"joined_{day}.csv"
    out_path = Path(args.out_path) if args.out_path else Path("runs") / "nba" / day / f"joined_with_phit_{day}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[add_p_hit_v0] day={day}")
    print(f"[add_p_hit_v0] in_path={in_path}")
    print(f"[add_p_hit_v0] out_path={out_path}")

    add_p_hit(in_path, out_path)

    print(f"[add_p_hit_v0] wrote {out_path}")


if __name__ == "__main__":
    main()
