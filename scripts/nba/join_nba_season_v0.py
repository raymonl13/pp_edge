#!/usr/bin/env python3
"""
join_nba_season_v0.py

Join a PrizePicks NBA board for a given day with real NBA season features
(data/nba/features/season_2025_features.csv) using name+team keys.

This is an external ETL-style join to produce a joined_{DAY}.csv snapshot
for modeling / slipbuilding experiments.
"""

import argparse
import csv
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple


def norm_name(name: str) -> str:
    """
    Normalize a player name to a join key:
    - lowercased
    - strip accents
    - keep only alphanumeric chars
    """
    if not isinstance(name, str):
        return ""
    # strip accents
    n = unicodedata.normalize("NFKD", name)
    n = "".join(ch for ch in n if not unicodedata.combining(ch))
    # lowercase and keep alnum
    n = "".join(ch.lower() for ch in n if ch.isalnum())
    return n


def load_board(board_path: Path) -> List[Dict[str, Any]]:
    if not board_path.exists():
        raise FileNotFoundError(f"Board file not found: {board_path}")
    raw = json.loads(board_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Board file {board_path} must be a JSON list.")
    return raw


def load_features(features_path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Load season features CSV and index by (normName, team, season).
    """
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")

    feats_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    with features_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("playerName", "") or ""
            team = row.get("team", "") or ""
            season = row.get("season", "") or ""
            if not name or not team:
                continue
            key = (norm_name(name), team.strip())
            # If there are multiple seasons, you can add season to the key later
            feats_by_key[key] = row
    return feats_by_key


def join_board_and_features(
    board_rows: List[Dict[str, Any]],
    feats_by_key: Dict[Tuple[str, str], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    joined: List[Dict[str, Any]] = []

    for row in board_rows:
        player_name = str(row.get("player_name", "") or "")
        team = str(row.get("team", "") or "").strip()
        key = (norm_name(player_name), team)
        feats = feats_by_key.get(key)

        out: Dict[str, Any] = dict(row)  # start with board row
        if feats:
            out["features_found"] = True
            # copy selected feature fields
            for col in [
                "games",
                "minutesPg",
                "points",
                "totalRb",
                "assists",
                "steals",
                "blocks",
                "per",
                "tsPercent",
                "usagePercent",
                "totalRBPercent",
                "assistPercent",
                "stealPercent",
                "blockPercent",
                "winShares",
                "vorp",
            ]:
                out[col] = feats.get(col)
        else:
            out["features_found"] = False

        joined.append(out)

    return joined


def write_joined_csv(joined_rows: List[Dict[str, Any]], out_path: Path) -> None:
    """
    Write joined rows to CSV. Fields = union of all keys across rows.
    """
    # Gather all fieldnames
    fieldnames: List[str] = []
    seen = set()
    for row in joined_rows:
        for k in row.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in joined_rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Join NBA PP board with season features into joined_{DAY}.csv")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--board-path", help="Path to board_{DAY}.json")
    parser.add_argument("--features-path", help="Path to season features CSV")
    parser.add_argument("--out-path", help="Output CSV path (default: runs/nba/{DAY}/joined_{DAY}.csv)")
    args = parser.parse_args()

    day = args.day
    board_path = Path(args.board_path) if args.board_path else Path("runs") / "nba" / day / f"board_{day}.json"
    features_path = Path(args.features_path) if args.features_path else Path("data") / "nba" / "features" / "season_2025_features.csv"
    out_path = Path(args.out_path) if args.out_path else Path("runs") / "nba" / day / f"joined_{day}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[join_nba_season_v0] day={day}")
    print(f"[join_nba_season_v0] board_path={board_path}")
    print(f"[join_nba_season_v0] features_path={features_path}")
    print(f"[join_nba_season_v0] out_path={out_path}")

    board_rows = load_board(board_path)
    feats_by_key = load_features(features_path)
    joined_rows = join_board_and_features(board_rows, feats_by_key)
    write_joined_csv(joined_rows, out_path)

    print(f"[join_nba_season_v0] wrote {out_path} rows={len(joined_rows)}")


if __name__ == "__main__":
    main()
