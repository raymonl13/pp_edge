# pp_edge_scraper.py  – one-file public-feed harvester
import requests, json, datetime, time, sys, pathlib

PP_URL = "https://api.prizepicks.com/projections"
VC_KEY = "MTL7WHHETXEX6XZJRUJNTJL5X"              # ← YOUR VisualCrossing key
UA      = "Mozilla/5.0 (Macintosh) Chrome/135 Safari/537.36"

HEADERS = {
    "User-Agent": UA,
    "x-device-id": "44e7b131-7d1f-4f72-888d-07eb2e2be499"
}

def _get(url, params=None, ok_status=(200,)):
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    if r.status_code not in ok_status:
        raise requests.HTTPError(f"{r.status_code} {r.text[:120]}")
    return r.json()

def fetch_pp_projections():
    params = dict(
        league_id=2, per_page=250, single_stat=True,
        in_game=True, state_code="CA", game_mode="pickem"
    )
    data = _get(PP_URL, params)
    return data["data"]          # list of projections   (403? try again after 1 s)

def fetch_lineups(date_iso):
    url = "https://rotowire.com/lineups/api/scheduled"
    return _get(url, params={"date": date_iso})

# --------------- assemble feeds -----------------

def save_feeds(date_iso):
    print(f"⏳  pulling feeds for {date_iso}")
    feeds = {}

    # 1️⃣ projections
    tries = 0
    while True:
        try:
            feeds["props_raw"] = fetch_pp_projections()
            break
        except requests.HTTPError as e:
            if e.response.status_code == 403 and tries < 2:
                tries += 1; time.sleep(1); continue
            raise

    # 2️⃣ board+icon (build locally: icon → odds_type ['demon','goblin','std'])
    feeds["board"] = [
        dict(prop_id=p["id"], variant=p["attributes"]["odds_type"].capitalize())
        for p in feeds["props_raw"]
    ]

    # 3️⃣ fake “true” lines (not provided in free endpoint → copy house line)
    feeds["lines_full"] = [
        dict(prop_id=p["id"], threshold=p["attributes"]["line_score"])
        for p in feeds["props_raw"]
    ]

    # 4️⃣ line-ups
    try:
        feeds["lineups"] = fetch_lineups(date_iso)
    except Exception as e:
        print("⚠️  line-ups fetch failed → blank", e)
        feeds["lineups"] = {}

    # 5️⃣ weather (park lat/lon list)
    parks = {
        "Fenway Park":  ("42.3467", "-71.0972"),
        "Dodger Stadium": ("34.0739", "-118.24"),
    }
    wx = {}
    for name,(lat,lon) in parks.items():
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/timeline/{lat},{lon}/{date_iso}"
        try:
            wx[name] = _get(url, params={
                "key": VC_KEY, "unitGroup": "us",
                "include": "hours", "contentType": "json"
            })
        except Exception as e:
            print(f"⚠️  WX {name} →", e)
    feeds["weather"] = wx

    # ➜ dump
    path = pathlib.Path("feeds")/f"live_feeds_{date_iso}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(feeds))
    print(f"✅  {path.name} written · {len(feeds['props_raw'])} props")

# CLI helper
if __name__ == "__main__":
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    save_feeds(day)
