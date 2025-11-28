#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import requests
import yaml


ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"


def _log(msg: str) -> None:
    print(f"[build_points_train_from_espn_v0] {msg}", file=sys.stderr)


def _norm_name(s: str) -> str:
    return "".join(ch.lower() for ch in str(s) if ch.isalnum())


@dataclass
class PlayerPoints:
    day: str
    player: str
    team: str
    actual_points: float
    player_key: str
    team_key: str


def _load_json_cached(url: str, cache_path: Path, params: Optional[dict] = None) -> dict:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    cache_path.write_text(json.dumps(data))
    return data


def _yyyymmdd(day: str) -> str:
    return day.replace("-", "")


def _load_aliases(path: Path) -> Dict[str, Dict[str, str]]:
    """
    Load player/team alias map from YAML.

    players: normalized_player_key -> canonical_normalized_player_key
    teams:   team_abbrev -> canonical_team_abbrev
    """
    if not path.exists():
        return {"players": {}, "teams": {}}
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    players = data.get("players") or {}
    teams = data.get("teams") or {}
    return {"players": dict(players), "teams": dict(teams)}


def _apply_player_alias(raw_name: str, player_aliases: Dict[str, str]) -> str:
    key = _norm_name(raw_name)
    return player_aliases.get(key, key)


def _apply_team_alias(raw_abbr: str, team_aliases: Dict[str, str]) -> str:
    abbr = (raw_abbr or "").upper()
    return team_aliases.get(abbr, abbr)


def _collect_completed_events_for_day(day: str, raw_dir: Path) -> List[str]:
    date_str = _yyyymmdd(day)
    cache_path = raw_dir / f"scoreboard_{date_str}.json"
    data = _load_json_cached(
        ESPN_SCOREBOARD_URL,
        cache_path,
        params={"dates": date_str},
    )
    events = data.get("events") or []
    event_ids: List[str] = []
    for ev in events:
        ev_id = ev.get("id")
        status = (ev.get("status") or {}).get("type") or {}
        state = status.get("state")
        completed = status.get("completed", False)
        if not ev_id:
            continue
        if not completed and state not in ("post", "final"):
            continue
        event_ids.append(str(ev_id))
    _log(f"day={day} completed_events={event_ids}")
    return event_ids


def _extract_points_from_summary(
    event_id: str,
    raw_dir: Path,
    day: str,
    player_aliases: Dict[str, str],
    team_aliases: Dict[str, str],
) -> List[PlayerPoints]:
    cache_path = raw_dir / f"summary_{event_id}.json"
    data = _load_json_cached(
        ESPN_SUMMARY_URL,
        cache_path,
        params={"event": event_id},
    )

    box = data.get("boxscore") or {}
    players_blocks = box.get("players") or []
    rows: List[PlayerPoints] = []

    for team_block in players_blocks:
        team_info = team_block.get("team") or {}
        team_abbr = (team_info.get("abbreviation") or "").upper()
        team_key = _apply_team_alias(team_abbr, team_aliases)

        stats_meta = team_block.get("statistics") or []
        if not stats_meta:
            _log(f"event={event_id} team={team_abbr} WARNING: no statistics table; skipping team")
            continue

        stat_table = stats_meta[0]
        labels = stat_table.get("labels") or []
        if not labels:
            _log(f"event={event_id} team={team_abbr} WARNING: no labels on stat_table; skipping team")
            continue

        lower_labels = [str(lbl).lower() for lbl in labels]
        pts_idx: Optional[int] = None
        for idx, lbl in enumerate(lower_labels):
            if "pts" == lbl.strip() or ("points" in lbl and "3pt" not in lbl and "three" not in lbl):
                pts_idx = idx
                break

        if pts_idx is None:
            _log(f"event={event_id} team={team_abbr} WARNING: no PTS column in labels={labels}; skipping team")
            continue

        for ath_entry in stat_table.get("athletes") or []:
            athlete = ath_entry.get("athlete") or {}
            name = athlete.get("displayName") or athlete.get("fullName") or ""
            stats = ath_entry.get("stats") or []
            if pts_idx >= len(stats):
                continue
            try:
                pts = float(stats[pts_idx])
            except (TypeError, ValueError):
                continue

            player_key = _apply_player_alias(name, player_aliases)
            rows.append(
                PlayerPoints(
                    day=day,
                    player=name,
                    team=team_abbr,
                    actual_points=pts,
                    player_key=player_key,
                    team_key=team_key,
                )
            )

    return rows


def _collect_boxscores_for_day(
    day: str,
    raw_dir: Path,
    player_aliases: Dict[str, str],
    team_aliases: Dict[str, str],
) -> pd.DataFrame:
    event_ids = _collect_completed_events_for_day(day, raw_dir)
    all_rows: List[PlayerPoints] = []
    for ev_id in event_ids:
        all_rows.extend(_extract_points_from_summary(ev_id, raw_dir, day, player_aliases, team_aliases))

    if not all_rows:
        _log(f"day={day} WARNING: no player points collected from ESPN")
        return pd.DataFrame(columns=["day", "player", "team", "actual_points", "player_key", "team_key"])

    df = pd.DataFrame(
        [
            {
                "day": r.day,
                "player": r.player,
                "team": r.team,
                "actual_points": r.actual_points,
                "player_key": r.player_key,
                "team_key": r.team_key,
            }
            for r in all_rows
        ]
    )
    return df


def _pick_player_column(df: pd.DataFrame, joined_path: Path) -> pd.DataFrame:
    candidates = [
        "player",
        "player_name",
        "player_full_name",
        "athlete",
        "athlete_name",
        "name",
        "prop_name",
    ]
    for col in candidates:
        if col in df.columns:
            if col != "player":
                _log(f"{joined_path} using '{col}' as player column")
                df = df.rename(columns={col: "player"})
            return df
    raise SystemExit(
        f"[build_points_train_from_espn_v0] joined CSV missing any player-name column "
        f"(tried {candidates}) in {joined_path}"
    )


def _load_joined_points_for_day(
    day: str,
    root: Path,
    player_aliases: Dict[str, str],
    team_aliases: Dict[str, str],
) -> pd.DataFrame:
    runs_dir = root / "runs" / "nba" / day
    candidates = [
        runs_dir / f"joined_with_phit_{day}.csv",
        runs_dir / f"joined_{day}.csv",
    ]

    joined_path: Optional[Path] = None
    for path in candidates:
        if path.exists():
            joined_path = path
            break

    if joined_path is None:
        raise SystemExit(
            f"[build_points_train_from_espn_v0] no joined CSV found for {day} "
            f"(looked for joined_with_phit_{day}.csv and joined_{day}.csv)"
        )

    df = pd.read_csv(joined_path)
    df = _pick_player_column(df, joined_path)

    if "market" in df.columns:
        mcol = "market"
    elif "market_norm" in df.columns:
        mcol = "market_norm"
    else:
        raise SystemExit(f"[build_points_train_from_espn_v0] no 'market' or 'market_norm' in {joined_path}")

    pts = df[df[mcol].astype(str).str.lower() == "points"].copy()
    if pts.empty:
        _log(f"day={day} NOTE: no Points rows in {joined_path}")
        return pts

    # Normalize team, then apply aliases
    if "team" in pts.columns:
        pts["team_key"] = pts["team"].astype(str).str.upper()
    else:
        pts["team_key"] = ""
    pts["team_key"] = pts["team_key"].map(lambda x: _apply_team_alias(x, team_aliases))

    # Normalize player, then apply aliases
    pts["player_key"] = pts["player"].astype(str).map(lambda x: _apply_player_alias(x, player_aliases))

    pts["day"] = day
    return pts


def build_points_train(
    days: List[str],
    root: Path,
    out_path: Path,
    raw_dir: Path,
    aliases_cfg: Dict[str, Dict[str, str]],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    unmatched_dir = root / "data/nba/modeling/unmatched"
    unmatched_dir.mkdir(parents=True, exist_ok=True)

    player_aliases = aliases_cfg.get("players", {})
    team_aliases = aliases_cfg.get("teams", {})

    all_train_rows: List[pd.DataFrame] = []

    for day in days:
        _log(f"processing DAY={day}")
        joined_pts = _load_joined_points_for_day(day, root, player_aliases, team_aliases)
        if joined_pts.empty:
            continue

        box_df = _collect_boxscores_for_day(day, raw_dir, player_aliases, team_aliases)
        if box_df.empty:
            _log(f"day={day} WARNING: no ESPN boxscore data; skipping")
            continue

        on_cols = ["player_key"]
        if "team_key" in box_df.columns and joined_pts["team_key"].nunique() > 1:
            on_cols = ["player_key", "team_key"]

        merged = joined_pts.merge(
            box_df,
            on=on_cols,
            how="left",
            suffixes=("", "_espn"),
        )

        missing = merged["actual_points"].isna().sum()
        if missing:
            _log(
                f"day={day} WARNING: {missing} Points rows could not be matched to ESPN boxscores; "
                f"writing unmatched report"
            )
            unmatched = merged[merged["actual_points"].isna()].copy()
            unmatched_path = unmatched_dir / f"unmatched_points_{day}.csv"
            unmatched.to_csv(unmatched_path, index=False)

        merged = merged[merged["actual_points"].notna()].copy()
        if merged.empty:
            _log(f"day={day} NOTE: after drop-missing, no training rows remain")
            continue

        merged["actual_points"] = merged["actual_points"].astype(float)
        merged["line"] = merged["line"].astype(float)
        merged["hit"] = (merged["actual_points"] > merged["line"]).astype(int)

        keep_cols = ["day", "player", "team", "line", "actual_points", "hit"]
        for extra in ["season_pts_per_game", "minutes_proj", "pts_per_min"]:
            if extra in merged.columns:
                keep_cols.append(extra)

        train_df = merged[keep_cols].copy()
        all_train_rows.append(train_df)

    if not all_train_rows:
        raise SystemExit("[build_points_train_from_espn_v0] no training rows collected for any day; nothing to write")

    out_df = pd.concat(all_train_rows, ignore_index=True)
    out_df.to_csv(out_path, index=False)
    _log(f"wrote {len(out_df)} rows to {out_path}")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Build NBA Points training CSV by merging joined_<DAY>.csv "
            "with ESPN scoreboard/summary boxscores."
        )
    )
    ap.add_argument(
        "--days",
        required=True,
        help="Comma-separated list of days, e.g. '2025-11-13,2025-11-16'.",
    )
    ap.add_argument(
        "--out",
        default="data/nba/modeling/points_train_v1.csv",
        help="Output training CSV path.",
    )
    ap.add_argument(
        "--raw-dir",
        default="data/nba/espn_raw",
        help="Directory for cached ESPN JSON (default: data/nba/espn_raw).",
    )
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    days = [d.strip() for d in args.days.split(",") if d.strip()]
    if not days:
        raise SystemExit("[build_points_train_from_espn_v0] --days must list at least one day")
    root = Path(".").resolve()
    out_path = root / args.out
    raw_dir = root / args.raw_dir

    aliases_cfg = _load_aliases(root / "config/nba_aliases_v1.yaml")
    build_points_train(days, root, out_path, raw_dir, aliases_cfg)


if __name__ == "__main__":
    main()
