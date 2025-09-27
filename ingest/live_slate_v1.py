import os, datetime as _dt
from typing import List, Dict, Optional
import requests
REQUIRED_ENV = ("LIVE_API_URL", "LIVE_API_KEY")
def _require_live_guard(source: str):
    if os.getenv("PP_EDGE_TEST_MODE") == "1":
        return
    if os.getenv("PP_EDGE_LIVE") != "1":
        raise RuntimeError("Refusing live run: set PP_EDGE_LIVE=1 to enable.")
    if source == "http":
        missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing required env(s) for live ingest: {', '.join(missing)}")
def _validate_date(date_str: str) -> str:
    try: _dt.datetime.strptime(date_str, "%Y-%m-%d")
    except Exception: raise ValueError("date must be YYYY-MM-DD")
    return date_str
def _normalize_legs(raw: List[Dict]) -> List[Dict]:
    legs = []
    for r in raw:
        player = r.get("player") or r.get("name") or r.get("player_name")
        gid = r.get("game_id") or r.get("gameId") or r.get("event_id") or r.get("match_id")
        p_hit = r.get("p_hit") or r.get("prob") or r.get("probability")
        edge = r.get("edge_pp") or r.get("edge") or r.get("ev") or 0.0
        tag = r.get("tag")
        cgroup = r.get("correlation_group") or r.get("team_id") or r.get("team")
        if player is None or gid is None or p_hit is None:
            continue
        legs.append({
            "player": player,
            "game_id": str(gid),
            "p_hit": float(p_hit),
            "edge_pp": float(edge),
            **({"tag": tag} if tag else {}),
            **({"correlation_group": cgroup} if cgroup else {}),
        })
    return legs
def fetch_slate(date: str, sport: str, source: str = "http", session: Optional[requests.Session] = None) -> List[Dict]:
    _require_live_guard(source)
    date = _validate_date(date)
    sport = sport.upper()
    if sport not in ("MLB", "NFL"):
        raise ValueError("sport must be MLB or NFL")
    if source == "fake":
        import json, pathlib
        p = os.getenv("LIVE_FAKE_PATH")
        if not p or not pathlib.Path(p).exists():
            raise FileNotFoundError("LIVE_FAKE_PATH not set or file missing")
        raw = json.loads(pathlib.Path(p).read_text())
        return _normalize_legs(raw)
    url = os.environ["LIVE_API_URL"]
    key = os.environ["LIVE_API_KEY"]
    sess = session or requests.Session()
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    params = {"date": date, "sport": sport}
    resp = sess.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    if not isinstance(data, list):
        raise ValueError("API response not a list; add a provider adapter")
    return _normalize_legs(data)
