#!/usr/bin/env python3
"""
Join NBA board + features + placeholder model to produce joined_{DAY}.csv.

This is v0.1 and uses a simple logistic transform of (recent stat - line) as a
stand-in for a real model. See docs/slp/nba_adapter_v0.md and Data Model v1.2.
"""

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def load_board(path: Path) -> pd.DataFrame:
    df = pd.read_json(path)
    required = ["player_name", "team", "game_date", "market", "line", "odds_type"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing board columns: {missing}")
    return df


def load_features(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    return pd.read_csv(path)


def join_board_feats(board: pd.DataFrame, feats: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    key = ["player_id", "team"] if "player_id" in board.columns else ["player_name", "team"]
    joined = board.merge(feats, on=key, how="left", suffixes=("", "_feat"))
    missing = joined[joined["mp_last3"].isna()].copy()
    return joined, missing


def simple_p_hit(row: pd.Series) -> float:
    market = str(row.get("market", "")).lower()
    line = float(row.get("line", 0.0) or 0.0)
    stat = row.get("pts_last5", np.nan)
    if "reb" in market:
        stat = row.get("reb_last5", np.nan)
    elif "ast" in market:
        stat = row.get("ast_last5", np.nan)
    if pd.isna(stat):
        return 0.5
    k = 0.25
    delta = float(stat) - line
    return float(1.0 / (1.0 + np.exp(-k * delta)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Join NBA board + features + model stub.")
    parser.add_argument("--day", required=True, help="Day (YYYY-MM-DD)")
    parser.add_argument("--board-path", required=True)
    parser.add_argument("--features-path", required=True)
    parser.add_argument("--out-path", required=True)
    args = parser.parse_args()

    board_path = Path(args.board_path)
    feats_path = Path(args.features_path)
    out_path = Path(args.out_path)

    board = load_board(board_path)
    feats = load_features(feats_path)
    joined, missing = join_board_feats(board, feats)
    if not missing.empty:
        miss_path = out_path.with_name("missing_features.csv")
        missing.to_csv(miss_path, index=False)
        print(f"[join_nba_v0] WARNING: {len(missing)} rows missing features; wrote {miss_path}")

    joined = joined.copy()
    joined["p_hit"] = joined.apply(simple_p_hit, axis=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joined.to_csv(out_path, index=False)
    print(f"[join_nba_v0] wrote {out_path} rows={len(joined)}")


if __name__ == "__main__":
    main()
