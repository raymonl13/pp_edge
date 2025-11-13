#!/usr/bin/env python3
"""
NBA board ingestion (v0.1, file-first, no network).

Reads a provider-specific NBA board JSON from disk and writes a normalized
board_{DAY}.json file under runs/nba/{DAY}/ as described in docs/slp/nba_adapter_v0.md.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a raw provider record into the normalized schema.

    REQUIRED keys:

        player_id   : str
        player_name : str
        team        : str
        opp_team    : str
        game_id     : str
        game_date   : str (YYYY-MM-DD)
        market      : str ("points","rebounds","assists","threes","pra",...)
        line        : float
        odds_type   : str ("standard","goblin","demon","flex",...)
        book        : str ("prizepicks",...)

    TODO: Replace the mapping below with your provider's real JSON fields.
    """
    player = raw.get("player", {}) if isinstance(raw.get("player", {}), dict) else {}
    return {
        "player_id": str(player.get("id", "")),
        "player_name": player.get("name", ""),
        "team": player.get("team", ""),
        "opp_team": raw.get("opponent", ""),
        "game_id": raw.get("game_id", ""),
        "game_date": raw.get("date", ""),
        "market": raw.get("stat_type", ""),
        "line": float(raw.get("line", 0.0) or 0.0),
        "odds_type": str(raw.get("odds_type", "standard")),
        "book": str(raw.get("book", "prizepicks")),
    }


def load_raw_board(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Raw board file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "data" in data:
        return list(data["data"])
    if isinstance(data, list):
        return list(data)
    raise ValueError("Unsupported raw board structure; expected list or dict['data'].")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize NBA board into board_{DAY}.json")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--raw-path", required=True, help="Path to raw provider board JSON")
    parser.add_argument("--out-dir", help="Output dir (default: runs/nba/{DAY})")
    args = parser.parse_args()

    day = args.day
    raw_path = Path(args.raw_path)
    out_dir = Path(args.out_dir) if args.out_dir else Path("runs") / "nba" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_records = load_raw_board(raw_path)
    normalized = [normalize_record(r) for r in raw_records]

    out_path = out_dir / f"board_{day}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ingest_nba_board] wrote {out_path} rows={len(normalized)}")


if __name__ == "__main__":
    from pathlib import Path
    main()
