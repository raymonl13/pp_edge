#!/usr/bin/env python3
"""
build_slips_nba_v0.py

Use SlipBuilder v2 to build NBA PrizePicks slips for a given day from
joined_with_phit_{DAY}.csv.

Inputs:
  - config_pp_edge_v6.8.yaml
  - runs/nba/{DAY}/joined_with_phit_{DAY}.csv

Outputs:
  - runs/nba/{DAY}/slips_nba_v0.json
  - runs/nba/{DAY}/slips_nba_v0.csv

NOTE:
  - v0.1: p_hit is a stub from season stats (see add_p_hit_v0.py).
  - We cap candidate legs and restrict to a small set of slip types (Power6, Power4)
    to avoid combinatorial explosion.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from code_utils_slipbuilder_v2 import SlipBuilder  # type: ignore


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def is_core_market(m: str) -> bool:
    """Keep markets where the p_hit stub is least insane."""
    m = m.lower()
    if "1st" in m or "first" in m or "minutes" in m or "quarter" in m:
        return False
    if m in ("points", "rebounds", "assists", "fantasy score"):
        return True
    if "pts+rebs+asts" in m or "pra" in m:
        return True
    if "pts+rebs" in m or "pts+asts" in m or "rebs+asts" in m:
        return True
    if "3-pt" in m or "3 pt" in m or "3pt" in m or "threes" in m:
        return True
    return False


def load_cfg(cfg_path: Path) -> Dict[str, Any]:
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    # For NBA v0.1, restrict to Power6/Power4 to keep combinatorics sane
    pouts = cfg.get("payouts", {})
    cfg["payouts"] = {k: v for k, v in pouts.items() if k in ("Power6", "Power4")}
    # Hard cap for NBA v0.1; override via cfg if desired
    cfg.setdefault("max_candidate_legs_nba", 25)
    return cfg


def load_legs(joined_path: Path, cfg: Dict[str, Any], min_games: int = 5) -> List[Dict[str, Any]]:
    if not joined_path.exists():
        raise FileNotFoundError(f"Joined-with-p_hit file not found: {joined_path}")

    min_edge_pp = float(cfg.get("min_edge_pp", 0.0))
    max_legs = int(cfg.get("max_candidate_legs_nba", 25))

    all_legs: List[Dict[str, Any]] = []

    with joined_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features_found = str(row.get("features_found", "")).strip().lower() == "true"
            if not features_found:
                continue

            games = safe_float(row.get("games"), 0.0)
            if games < min_games:
                continue

            market = (row.get("market") or "").lower()
            if not is_core_market(market):
                continue

            p_hit = safe_float(row.get("p_hit"), 0.5)
            edge_pp = p_hit - 0.5
            if edge_pp < min_edge_pp:
                continue

            odds_type = (row.get("odds_type") or "").lower()
            tag = "Demon" if odds_type == "demon" else None

            player_name = row.get("player_name") or ""
            team = row.get("team") or ""
            game_id = row.get("game_id") or ""

            leg: Dict[str, Any] = dict(row)
            leg["player"] = f"{player_name} ({team})"
            leg["game_id"] = game_id
            leg["p_hit"] = p_hit
            leg["edge_pp"] = edge_pp
            if tag:
                leg["tag"] = tag

            all_legs.append(leg)

    # Sort by edge_pp and cap to max_legs to avoid combinatorial explosion
    all_legs.sort(key=lambda l: l["edge_pp"], reverse=True)
    legs = all_legs[:max_legs]

    print(f"[build_slips_nba_v0] loaded {len(all_legs)} candidate legs from {joined_path}")
    print(f"[build_slips_nba_v0] using top {len(legs)} legs (max_candidate_legs_nba={max_legs}) after sorting by edge_pp")
    return legs


def summarize_slips(slips: List[Dict[str, Any]], out_json: Path, out_csv: Path) -> None:
    out_json.write_text(json.dumps(slips, ensure_ascii=False, indent=2))
    print(f"[build_slips_nba_v0] wrote {out_json}")

    fieldnames = ["slip_type", "edge_pp", "stake_total", "num_legs", "legs_summary"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for slip in slips:
            legs = slip.get("legs", [])
            legs_summary = "; ".join(
                f"{l.get('player_name','?')} ({l.get('team','')}) {l.get('market','')} {l.get('line','')}"
                for l in legs
            )
            row = {
                "slip_type": slip.get("slip_type"),
                "edge_pp": slip.get("edge_pp"),
                "stake_total": slip.get("stake_total"),
                "num_legs": len(legs),
                "legs_summary": legs_summary,
            }
            writer.writerow(row)
    print(f"[build_slips_nba_v0] wrote {out_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build NBA slips using SlipBuilder v2 for a given day.")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--joined-path", help="Input joined_with_phit CSV (default: runs/nba/{DAY}/joined_with_phit_{DAY}.csv)")
    parser.add_argument("--cfg-path", help="Config path (default: config_pp_edge_v6.8.yaml)")
    parser.add_argument("--out-json", help="Output slips JSON (default: runs/nba/{DAY}/slips_nba_v0.json)")
    parser.add_argument("--out-csv", help="Output slips CSV (default: runs/nba/{DAY}/slips_nba_v0.csv)")
    parser.add_argument("--min-games", type=int, default=5, help="Minimum games to include a player (default: 5)")
    args = parser.parse_args()

    day = args.day
    joined_path = Path(args.joined_path) if args.joined_path else Path("runs") / "nba" / day / f"joined_with_phit_{day}.csv"
    cfg_path = Path(args.cfg_path) if args.cfg_path else REPO_ROOT / "config_pp_edge_v6.8.yaml"
    out_json = Path(args.out_json) if args.out_json else Path("runs") / "nba" / day / "slips_nba_v0.json"
    out_csv = Path(args.out_csv) if args.out_csv else Path("runs") / "nba" / day / "slips_nba_v0.csv"

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    print(f"[build_slips_nba_v0] day={day}")
    print(f"[build_slips_nba_v0] joined_path={joined_path}")
    print(f"[build_slips_nba_v0] cfg_path={cfg_path}")
    print(f"[build_slips_nba_v0] out_json={out_json}")
    print(f"[build_slips_nba_v0] out_csv={out_csv}")

    cfg = load_cfg(cfg_path)
    legs = load_legs(joined_path, cfg, min_games=args.min_games)

    if not legs:
        print("[build_slips_nba_v0] No candidate legs after filters; exiting.")
        return

    builder = SlipBuilder(cfg)
    slips = builder.build_slips(legs)
    print(f"[build_slips_nba_v0] built {len(slips)} slips")

    summarize_slips(slips, out_json, out_csv)


if __name__ == "__main__":
    main()
