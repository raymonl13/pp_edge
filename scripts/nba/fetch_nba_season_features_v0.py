#!/usr/bin/env python3
"""
fetch_nba_season_features_v0.py

Fetches real NBA season totals + advanced stats from the public NBA Stats API
(nprasad2077/nbaStats) and writes a merged features CSV suitable for joining
to the PrizePicks NBA board.

Data source:
  https://api.server.nbaapi.com/api/playertotals
  https://api.server.nbaapi.com/api/playeradvancedstats

NOTE:
- This is an external ETL step. It should be run manually (or via a cron/CI job)
  to populate data/nba/features/... for the PP-EDGE engine to consume.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import requests

BASE_URL = "https://api.server.nbaapi.com"
SEASON = 2025  # adjust if you want a different season
PAGE_SIZE = 200  # max per response; API defaults to 20


def fetch_all(endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch all pages for a given endpoint, returning a list of records.

    The API returns:
      { "data": [...], "pagination": { "page": ..., "pages": ..., ... } }
    """
    results: List[Dict[str, Any]] = []
    page = 1

    while True:
        p = dict(params)
        p.update({"page": page, "pageSize": PAGE_SIZE})
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, params=p, headers={"accept": "application/json"}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        data = payload.get("data", [])
        pagination = payload.get("pagination", {})
        total_pages = int(pagination.get("pages", page))

        results.extend(data)
        print(f"[fetch_all] {endpoint} page {page}/{total_pages}, got {len(data)} records")

        if page >= total_pages or not data:
            break
        page += 1

    print(f"[fetch_all] {endpoint} total records: {len(results)}")
    return results


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]  # scripts/nba/... → repo root
    raw_dir = repo_root / "data" / "nba" / "raw"
    feat_dir = repo_root / "data" / "nba" / "features"
    raw_dir.mkdir(parents=True, exist_ok=True)
    feat_dir.mkdir(parents=True, exist_ok=True)

    print(f"[fetch_nba_season_features_v0] repo_root={repo_root}")
    print(f"[fetch_nba_season_features_v0] season={SEASON}")

    # 1) Fetch totals and advanced
    totals = fetch_all("/api/playertotals", {"season": SEASON})
    adv = fetch_all("/api/playeradvancedstats", {"season": SEASON})

    # 2) Save raw JSON snapshots (for reproducibility)
    totals_path = raw_dir / f"player_totals_{SEASON}.json"
    adv_path = raw_dir / f"player_advanced_{SEASON}.json"
    totals_path.write_text(json.dumps(totals, ensure_ascii=False, indent=2))
    adv_path.write_text(json.dumps(adv, ensure_ascii=False, indent=2))
    print(f"[fetch_nba_season_features_v0] wrote {totals_path}")
    print(f"[fetch_nba_season_features_v0] wrote {adv_path}")

    # 3) Build a dict for advanced stats keyed by (playerName, team)
    adv_by_key: Dict[tuple, Dict[str, Any]] = {}
    for rec in adv:
        name = rec.get("playerName", "").strip()
        team = rec.get("team", "").strip()
        season = rec.get("season", SEASON)
        if not name or not team:
            continue
        key = (name, team, season)
        adv_by_key[key] = rec

    # 4) Merge totals + advanced into a flat features table
    features_path = feat_dir / f"season_{SEASON}_features.csv"
    fieldnames = [
        "playerName",
        "team",
        "season",
        # totals
        "games",
        "minutesPg",
        "points",
        "totalRb",
        "assists",
        "steals",
        "blocks",
        # advanced
        "per",
        "tsPercent",
        "usagePercent",
        "totalRBPercent",
        "assistPercent",
        "stealPercent",
        "blockPercent",
        "winShares",
        "vorp",
    ]

    with features_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        rows_written = 0
        for rec in totals:
            name = rec.get("playerName", "").strip()
            team = rec.get("team", "").strip()
            season = rec.get("season", SEASON)
            if not name or not team:
                continue
            key = (name, team, season)
            adv_rec = adv_by_key.get(key, {})

            row = {
                "playerName": name,
                "team": team,
                "season": season,
                # totals
                "games": rec.get("games"),
                "minutesPg": rec.get("minutesPg"),
                "points": rec.get("points"),
                "totalRb": rec.get("totalRb"),
                "assists": rec.get("assists"),
                "steals": rec.get("steals"),
                "blocks": rec.get("blocks"),
                # advanced
                "per": adv_rec.get("per"),
                "tsPercent": adv_rec.get("tsPercent"),
                "usagePercent": adv_rec.get("usagePercent"),
                "totalRBPercent": adv_rec.get("totalRBPercent"),
                "assistPercent": adv_rec.get("assistPercent"),
                "stealPercent": adv_rec.get("stealPercent"),
                "blockPercent": adv_rec.get("blockPercent"),
                "winShares": adv_rec.get("winShares"),
                "vorp": adv_rec.get("vorp"),
            }
            writer.writerow(row)
            rows_written += 1

    print(f"[fetch_nba_season_features_v0] wrote {features_path} rows={rows_written}")


if __name__ == "__main__":
    main()
