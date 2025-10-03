#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, json
from datetime import datetime, timedelta
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import requests, yaml

def _iso_day(s: str|None) -> str:
    if s: return s
    now = datetime.now(ZoneInfo("America/Los_Angeles")) if ZoneInfo else datetime.utcnow()
    return (now + timedelta(days=1)).date().isoformat()

def _cfg(p: str) -> dict:
    f = Path(p)
    if not f.exists(): return {}
    try:
        with f.open() as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}

def main() -> int:
    ap=argparse.ArgumentParser(description="Router smoke")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    ap.add_argument("--source")
    ap.add_argument("--date")
    args=ap.parse_args()

    cfg=_cfg(args.cfg)
    src = args.source or os.environ.get("ROUTER_SOURCE") or (cfg.get("router") or {}).get("source") or "http"
    day = _iso_day(args.date)
    url = os.environ.get("ROUTER_URL") or (cfg.get("router") or {}).get("url") or \
          "https://api.prizepicks.com/projections?league_id=2&per_page=1&date={date}&state_code=CO"
    url = url.replace("{date}", day)

    key = os.environ.get("ROUTER_API_KEY")
    headers={"User-Agent":"PP-EDGE/router_smoke"}
    if key:
        headers["Authorization"]=f"Bearer {key}"
        headers["X-API-Key"]=key

    info = {
        "has_api_key": bool(key),
        "source": src,
        "url_preview": url.replace(key, "REDACTED") if key else url,
        "auth_headers_present": [h for h in headers if h.lower() in ("authorization","x-api-key")],
        "status": None, "connectivity": None, "error": None,
    }

    if src in ("fake","board"):
        info.update(connectivity="skipped", status=200)
        print(json.dumps(info, indent=2)); return 0

    try:
        r = requests.head(url, timeout=6, headers=headers)
        if r.status_code >= 400:
            r = requests.get(url, timeout=6, headers=headers)
        info.update(status=r.status_code, connectivity="ok" if r.status_code<400 else "error")
    except Exception as e:
        info.update(connectivity="error", error=e.__class__.__name__)

    print(json.dumps(info, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
