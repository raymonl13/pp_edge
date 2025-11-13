#!/usr/bin/env python3
"""
NBA features v0.1 for Golden Day.

Reads an NBA gamelog CSV and produces per-player features:

- mp_last3, mp_last10
- usage_last10 (simple proxy)
- team_pace_last10 (optional)
- pts_last5, reb_last5, ast_last5

See docs/slp/nba_adapter_v0.md for details.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class Config:
    day: str
    gamelogs_path: Path
    out_path: Path
    pace_path: Optional[Path] = None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Build NBA features v0.1 for a given day.")
    parser.add_argument("--day", required=True, help="Target day (YYYY-MM-DD)")
    parser.add_argument("--gamelogs-path", required=True, help="Path to NBA gamelog CSV")
    parser.add_argument("--out-path", required=True, help="Output path for features (csv/parquet)")
    parser.add_argument("--pace-path", help="Optional path to team pace CSV")
    args = parser.parse_args()
    return Config(
        day=args.day,
        gamelogs_path=Path(args.gamelogs_path),
        out_path=Path(args.out_path),
        pace_path=Path(args.pace_path) if args.pace_path else None,
    )


def load_gamelogs(cfg: Config) -> pd.DataFrame:
    df = pd.read_csv(cfg.gamelogs_path)
    required = [
        "player_id", "player_name", "team", "game_date",
        "minutes", "pts", "reb", "ast"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required gamelog columns: {missing}")
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def filter_window(df: pd.DataFrame, cutoff: datetime, days_back: int) -> pd.DataFrame:
    start = cutoff - timedelta(days=days_back * 2)
    mask = (df["game_date"] < cutoff) & (df["game_date"] >= start)
    return df.loc[mask].copy()


def build_features(cfg: Config) -> pd.DataFrame:
    target_day = datetime.fromisoformat(cfg.day)
    logs = load_gamelogs(cfg)
    logs_before = logs[logs["game_date"] < target_day]

    def window_mean(col: str, window_games: int, alias: str) -> pd.DataFrame:
        dfw = filter_window(logs_before, target_day, window_games)
        grouped = (
            dfw.sort_values("game_date")
            .groupby(["player_id", "team"])
            .tail(window_games)
            .groupby(["player_id", "team"])[col]
            .mean()
            .rename(alias)
            .reset_index()
        )
        return grouped

    mp3 = window_mean("minutes", 3, "mp_last3")
    mp10 = window_mean("minutes", 10, "mp_last10")
    pts5 = window_mean("pts", 5, "pts_last5")
    reb5 = window_mean("reb", 5, "reb_last5")
    ast5 = window_mean("ast", 5, "ast_last5")

    base = (
        logs_before.sort_values("game_date")
        .groupby(["player_id", "team"], as_index=False)
        .tail(1)[["player_id", "player_name", "team", "game_date"]]
    )

    feats = base.merge(mp3, on=["player_id", "team"], how="left") \
                .merge(mp10, on=["player_id", "team"], how="left") \
                .merge(pts5, on=["player_id", "team"], how="left") \
                .merge(reb5, on=["player_id", "team"], how="left") \
                .merge(ast5, on=["player_id", "team"], how="left")

    # Simple usage proxy; refine later
    feats["usage_last10"] = (feats["pts_last5"] + feats["reb_last5"] + feats["ast_last5"]) / feats["mp_last10"].clip(lower=1)

    if cfg.pace_path and cfg.pace_path.exists():
        pace = pd.read_csv(cfg.pace_path)
        if "team" in pace.columns and "pace_last10" in pace.columns:
            feats = feats.merge(
                pace[["team", "pace_last10"]],
                on="team",
                how="left",
            )
            feats = feats.rename(columns={"pace_last10": "team_pace_last10"})
    else:
        feats["team_pace_last10"] = None

    return feats


def save_features(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() in {".parquet", ".pq"}:
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)
    print(f"[features_nba_v0] wrote {out_path} rows={len(df)}")


def main() -> None:
    cfg = parse_args()
    feats = build_features(cfg)
    save_features(feats, cfg.out_path)


if __name__ == "__main__":
    main()
