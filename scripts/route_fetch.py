#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, time, hashlib, traceback, random, math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import requests, yaml

def _now_pt() -> datetime:
    if ZoneInfo:
        return datetime.now(ZoneInfo("America/Los_Angeles"))
    return datetime.utcnow()

def _iso_day(day_arg: Optional[str]) -> str:
    return day_arg or (_now_pt() + timedelta(days=1)).date().isoformat()

def _read_yaml(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists(): return {}
    try:
        with p.open() as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def _provenance(script: Path) -> Dict[str, Any]:
    sha = hashlib.sha256(script.read_bytes()).hexdigest() if script.exists() else "missing"
    head = os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown"
    return {
        "script_path": str(script),
        "script_sha256_16": sha[:16] if sha != "missing" else "missing",
        "script_sha256": sha if sha != "missing" else "missing",
        "git_head": head,
        "ts_utc": datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds").replace("+00:00","Z"),
    }

def _headers() -> Dict[str, str]:
    h = {"User-Agent": "PP-EDGE/route_fetch"}
    key = os.environ.get("ROUTER_API_KEY")
    if key:
        h["Authorization"] = f"Bearer {key}"
        h["X-API-Key"] = key
    return h

def _sanitize_url(url: Optional[str]) -> Optional[str]:
    if not url: return url
    parsed = urlsplit(url)
    q = parse_qsl(parsed.query, keep_blank_values=True)
    red_keys = {"api_key","apikey","token","auth","authorization","key","x-api-key","x_api_key","x-api_key"}
    q2 = [(k, "REDACTED") if k.lower() in red_keys else (k, v) for k, v in q]
    safe = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(q2, doseq=True), parsed.fragment))
    key = os.environ.get("ROUTER_API_KEY")
    if key and key in safe:
        safe = safe.replace(key, "REDACTED")
    return safe

def _normalize_rows(obj: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if isinstance(obj, list):
        rows = obj
    elif isinstance(obj, dict):
        if "data" in obj:
            for o in obj.get("data", []):
                a = o.get("attributes", o)
                rows.append({
                    "player": str(a.get("player") or a.get("name","")),
                    "team":   str(a.get("team","")),
                    "stat":   str(a.get("stat") or a.get("stat_type","")).title(),
                    "line":   a.get("line", a.get("line_score", 0.0)),
                })
        elif "included" in obj:
            for o in obj.get("included", []):
                a = o.get("attributes", {})
                rows.append({
                    "player": str(a.get("name","")),
                    "team":   str(a.get("team","")),
                    "stat":   str(a.get("stat_type","")).title(),
                    "line":   a.get("line_score", 0.0),
                })
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            line = float(r.get("line", 0.0))
            if not math.isfinite(line):  # guard against NaN/inf
                continue
            out.append({
                "player": str(r.get("player","")),
                "team":   str(r.get("team","")),
                "stat":   str(r.get("stat","")).title(),
                "line":   line,
            })
        except Exception:
            continue
    return out

def _fake_board() -> List[Dict[str, Any]]:
    return [
        {"player":"Sample Hitter","team":"NYY","stat":"Hits","line":1.5},
        {"player":"Sample Pitcher","team":"HOU","stat":"Ks","line":5.5},
        {"player":"Sample Runner","team":"LAD","stat":"Bases","line":1.5},
        {"player":"Sample Batter","team":"ATL","stat":"Rbis","line":0.5},
    ]

def _resolve_source(cli_source: Optional[str], cfg: Dict[str,Any]) -> str:
    return (cli_source
            or os.environ.get("ROUTER_SOURCE")
            or (cfg.get("router") or {}).get("source")
            or "http")

def _resolve_url(day: str, cfg: Dict[str,Any]) -> Optional[str]:
    url = os.environ.get("ROUTER_URL") or (cfg.get("router") or {}).get("url")
    if not url:
        url = "https://api.prizepicks.com/projections?league_id=2&per_page=5000&date={date}&state_code=CO"
    return url.replace("{date}", day)

def _min_rows(args_min_rows: int, cfg: Dict[str,Any]) -> int:
    y = (cfg.get("router") or {}).get("min_rows")
    try:
        return int(y) if y is not None else int(args_min_rows)
    except Exception:
        return int(args_min_rows)

def _fetch_http(url: str, max_attempts: int, timeout: float) -> Tuple[Optional[Any], Dict[str,Any]]:
    status=None; attempts=0; t0=time.time(); last_exc=None
    disable_backoff = os.environ.get("ROUTER_BACKOFF_DISABLE") == "1"
    for i in range(1, max_attempts+1):
        attempts=i
        try:
            r = requests.get(url, headers=_headers(), timeout=timeout)
            status = r.status_code
            if status == 200:
                return r.json(), {"attempts": attempts, "http_status": status, "elapsed_ms": int((time.time()-t0)*1000)}
            if status not in (429,500,502,503):
                break
        except Exception as e:
            last_exc = e
        if not disable_backoff:
            base = min(2**i, 12)
            time.sleep(base * random.uniform(0.5, 1.5))
    diag = {"attempts": attempts, "http_status": status, "elapsed_ms": int((time.time()-t0)*1000)}
    if last_exc: diag["error"] = last_exc.__class__.__name__
    return None, diag

def _write_json_atomic_and_hash(path: Path, rows: List[Dict[str,Any]]) -> Tuple[str,str]:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(rows, indent=2))
    os.replace(tmp, path)
    full = hashlib.sha256(path.read_bytes()).hexdigest()
    return full, full[:16]

def main() -> int:
    ap = argparse.ArgumentParser(description="PP-EDGE router (Session 7)")
    ap.add_argument("--date")
    ap.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    ap.add_argument("--source")
    ap.add_argument("--min-rows", type=int, default=int(os.environ.get("ROUTER_MIN_ROWS","30")))
    ap.add_argument("--max-attempts", type=int, default=int(os.environ.get("ROUTER_MAX_ATTEMPTS","4")))
    ap.add_argument("--timeout", type=float, default=float(os.environ.get("ROUTER_TIMEOUT","12")))
    args = ap.parse_args()

    cfg   = _read_yaml(args.cfg)
    day   = _iso_day(args.date)
    src   = _resolve_source(args.source, cfg)
    url   = _resolve_url(day, cfg) if src == "http" else None
    min_rows = _min_rows(args.min_rows, cfg)

    out_dir = Path("data"); out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path("data/logs"); log_dir.mkdir(parents=True, exist_ok=True)
    target  = out_dir / f"pricefix_{day}.json"

    debug: Dict[str, Any] = {
        "source": src, "day": day, "url": _sanitize_url(url),
        "attempts": 0, "RETRY_COUNT": 0,
        "status": "INIT", "elapsed_ms": 0, "row_count": 0,
        "board_sha": None, "board_sha16": None,
        "ROUTE_STATE": None, "PROVIDER_STATE": None, "HTTP_STATUS": None,
        "ROUTE_NOOP": False,
        "provenance": _provenance(Path(__file__)),
        "env": {"has_api_key": bool(os.environ.get("ROUTER_API_KEY"))},
    }

    rows: List[Dict[str, Any]] = []
    try:
        if src == "fake":
            rows = _fake_board()
            debug.update(status="OK_FAKE", PROVIDER_STATE="SKIP", ROUTE_STATE="OK")
        elif src == "board":
            if target.exists():
                rows = json.loads(target.read_text())
                debug.update(status="OK_BOARD", PROVIDER_STATE="SKIP", ROUTE_STATE="OK", ROUTE_NOOP=True)
            else:
                rows = _fake_board()
                debug.update(status="MISSING_BOARD", PROVIDER_STATE="SKIP", ROUTE_STATE="DEGRADED")
        elif src == "http":
            obj, diag = _fetch_http(url, args.max_attempts, args.timeout)
            debug.update(attempts=diag.get("attempts",0),
                         RETRY_COUNT=diag.get("attempts",0),
                         elapsed_ms=diag.get("elapsed_ms",0),
                         HTTP_STATUS=diag.get("http_status"))
            if obj is None:
                debug.update(status="HTTP_FAIL", PROVIDER_STATE="ERROR", ROUTE_STATE="DEGRADED")
                if target.exists():
                    rows = json.loads(target.read_text())
                    debug["ROUTE_NOOP"] = True
                else:
                    rows = _fake_board()
            else:
                rows = _normalize_rows(obj)
                if len(rows) < min_rows:
                    debug.update(status="HTTP_TINY", PROVIDER_STATE="TINY", ROUTE_STATE="DEGRADED")
                    if target.exists():
                        rows = json.loads(target.read_text()); debug["ROUTE_NOOP"] = True
                    else:
                        rows = _fake_board()
                else:
                    debug.update(status="HTTP_OK", PROVIDER_STATE="OK", ROUTE_STATE="OK")
        else:
            debug.update(status="BAD_SOURCE", PROVIDER_STATE="SKIP", ROUTE_STATE="DEGRADED")
            rows = _fake_board()
    except Exception as e:
        debug.update(status="EXC", PROVIDER_STATE="ERROR", ROUTE_STATE="DEGRADED",
                     error=e.__class__.__name__, trace=traceback.format_exc(limit=2))
        rows = _fake_board()

    debug["row_count"] = len(rows)
    if debug.get("ROUTE_NOOP"):
        if target.exists():
            full = hashlib.sha256(target.read_bytes()).hexdigest()
            debug["board_sha"], debug["board_sha16"] = full, full[:16]
    else:
        full, short = _write_json_atomic_and_hash(target, rows)
        debug["board_sha"], debug["board_sha16"] = full, short

    summary = (
        f"[router] source={src} status={debug['status']} "
        f"route_state={debug['ROUTE_STATE']} rows={debug['row_count']} sha16={debug['board_sha16']}"
    )
    print(summary)
    (log_dir / "route_debug.json").write_text(json.dumps(debug, indent=2))
    (log_dir / "router_summary.txt").write_text(summary + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
