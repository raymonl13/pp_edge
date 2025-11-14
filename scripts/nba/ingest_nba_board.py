#!/usr/bin/env python3
"""
NBA board ingestion (v0.1, PrizePicks JSON API style).

Reads a PrizePicks NBA board JSON from disk and writes a normalized
runs/nba/{DAY}/board_{DAY}.json as described in docs/slp/nba_adapter_v0.md.

Handles JSON:API-like shape:

    { "data": [...projection/new_player/game...], "included": [...] }

and joins `projection` records to `new_player` (and optionally `game`) records.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_raw_board(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Load raw board JSON and split into projection / player / game lookups."""
    if not path.exists():
        raise FileNotFoundError(f"Raw board file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    data = doc.get("data", [])
    included = doc.get("included", [])

    projections: List[Dict[str, Any]] = []
    players: Dict[str, Dict[str, Any]] = {}
    games: Dict[str, Dict[str, Any]] = {}

    def register(item: Dict[str, Any]) -> None:
        rtype = item.get("type")
        rid = str(item.get("id", ""))
        attrs = item.get("attributes") or {}
        if rtype == "projection":
            projections.append(item)
        elif rtype == "new_player":
            players[rid] = attrs
        elif rtype == "game":
            games[rid] = attrs

    for item in data:
        if isinstance(item, dict):
            register(item)
    for item in included:
        if isinstance(item, dict):
            register(item)

    return projections, players, games


def normalize_projection(
    proj: Dict[str, Any],
    players: Dict[str, Dict[str, Any]],
    games: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize a single PrizePicks projection into the PP-EDGE board schema, skipping:
      - combo props (new_player.combo == True or stat_type containing 'Combo')
    """
    attrs = proj.get("attributes") or {}
    rels = proj.get("relationships") or {}

    event_type = attrs.get("event_type")  # 'team', 'combo', etc., kept for reference

    player_ref = (rels.get("new_player") or {}).get("data") or {}
    game_ref = (rels.get("game") or {}).get("data") or {}

    player_id = str(player_ref.get("id", ""))
    game_id_raw = str(game_ref.get("id", ""))

    player_attrs = players.get(player_id, {})
    game_attrs = games.get(game_id_raw, {})

    # Skip combos in v0.1 (true multi-player combos)
    if player_attrs.get("combo") is True:
        raise ValueError("Combo projection (new_player.combo==True); skipping for v0.1")

    raw_stat = str(attrs.get("stat_type") or attrs.get("stat_display_name") or "")
    if "combo" in raw_stat.lower():
        raise ValueError(f"Combo-like market '{raw_stat}'; skipping for v0.1")

    player_name = (
        player_attrs.get("display_name")
        or player_attrs.get("name")
        or ""
    )
    team = (
        player_attrs.get("team")
        or player_attrs.get("team_abbreviation")
        or attrs.get("description")
        or ""
    )

    start_time = game_attrs.get("start_time") or attrs.get("start_time") or ""
    board_time = attrs.get("board_time") or ""
    game_date = ""
    if isinstance(start_time, str) and len(start_time) >= 10:
        game_date = start_time[:10]
    elif isinstance(board_time, str) and len(board_time) >= 10:
        game_date = board_time[:10]

    home_team = game_attrs.get("home_team", "")
    away_team = game_attrs.get("away_team", "")
    opp_team = ""
    if team and home_team and away_team:
        if team == home_team:
            opp_team = away_team
        elif team == away_team:
            opp_team = home_team

    if home_team and away_team and game_date:
        game_id = f"{away_team}@{home_team}_{game_date}"
    else:
        game_id = attrs.get("game_id") or f"NBA_game_{game_id_raw}"

    stat_type = raw_stat
    market = stat_type.lower()
    if stat_type in ("Points", "Pts"):
        market = "points"
    elif stat_type in ("Rebounds", "Rebs"):
        market = "rebounds"
    elif "ast" in stat_type.lower():
        market = "assists"
    elif "3-PT" in stat_type or "3 PT" in stat_type or "3-PT Made" in stat_type:
        market = "threes"
    elif "pts+rebs+asts" in stat_type.lower() or stat_type.upper() == "PRA":
        market = "pra"

    line = float(attrs.get("line_score", 0.0) or 0.0)
    odds_type = str(attrs.get("odds_type", "standard"))

    return {
        "player_id": player_id,
        "player_name": player_name,
        "team": team,
        "opp_team": opp_team,
        "game_id": game_id,
        "game_date": game_date,
        "market": market,
        "line": line,
        "odds_type": odds_type,
        "book": "prizepicks",
    }


def normalize_board(
    projections: List[Dict[str, Any]],
    players: Dict[str, Dict[str, Any]],
    games: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Normalize all projections into the board schema, skipping only true combos."""
    out: List[Dict[str, Any]] = []
    for proj in projections:
        try:
            rec = normalize_projection(proj, players, games)
        except ValueError:
            continue
        out.append(rec)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize PrizePicks NBA board into board_{DAY}.json")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--raw-path", required=True, help="Path to raw PrizePicks board JSON")
    parser.add_argument("--out-dir", help="Output dir (default: runs/nba/{DAY})")
    args = parser.parse_args()

    day = args.day
    raw_path = Path(args.raw_path)
    out_dir = Path(args.out_dir) if args.out_dir else Path("runs") / "nba" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    projections, players, games = load_raw_board(raw_path)
    normalized = normalize_board(projections, players, games)

    out_path = out_dir / f"board_{day}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ingest_nba_board] wrote {out_path} rows={len(normalized)}")


if __name__ == "__main__":
    main()
