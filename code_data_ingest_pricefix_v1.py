#!/usr/bin/env python3
import argparse, datetime, json, os, requests, pandas as pd

GOOD_STATES = ["GA","TN","TX","CO","IL","DC","WY"]
BASE        = "https://api.prizepicks.com/projections"

def fetch_board(day_iso, st):
    url = f"{BASE}?league_id=2&per_page=5000&date={day_iso}&state_code={st}"
    r   = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date")
    p.add_argument("--state")
    args = p.parse_args()

    day  = args.date or (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    out  = f"data/pricefix_{day}.json"
    if os.path.exists(out):
        print("✓ board already present —", out)
        return

    states = [args.state] if args.state else GOOD_STATES
    for st in states:
        try:
            data = fetch_board(day, st)
            break
        except requests.HTTPError as e:
            if e.response.status_code != 403: raise
    else:
        raise SystemExit("❌ 403 from all states — try VPN or licensed-state IP")

    rows = [
        {
            "player": o["attributes"]["name"],
            "team":   o["attributes"]["team"],
            "stat":   o["attributes"]["stat_type"].title(),
            "line":   float(o["attributes"]["line_score"]),
        }
        for o in data["included"] if o["type"] == "new_player"
    ]
    os.makedirs("data", exist_ok=True)
    pd.DataFrame(rows).to_json(out, orient="records")
    print("✓ board saved →", out, "rows:", len(rows))

if __name__ == "__main__":
    main()
