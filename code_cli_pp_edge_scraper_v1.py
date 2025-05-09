#!/usr/bin/env python3
"""Thin CLI wrapper for PP Edge Scraper v1 (stub)"""

import argparse
import pathlib
import json

def scrape(query: str) -> dict:
    # TODO: implement real scraper
    return {"query": query, "dummy": True}

def main():
    ap = argparse.ArgumentParser(
        description="PP Edge Scraper v1 (stub)"
    )
    ap.add_argument(
        "query",
        help="date in YYYY-MM-DD or other query string"
    )
    args = ap.parse_args()

    out = scrape(args.query)

    # === write into your data/ folder ===
    root     = pathlib.Path(__file__).parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    filename = f"live_feeds_{args.query}.json"
    path     = data_dir / filename

    path.write_text(json.dumps(out, indent=2))
    print("✔️  wrote", path)

if __name__ == "__main__":
    main()
