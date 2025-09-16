# poll_slip_results.py
"""
Polling utility for slip results.

Contract (tests):
- ps.poll(csv_path) SHOULD create/write the CSV at csv_path when the GET returns rows.
- In test mode without network stubs, it should NOT create the file.

Production callers may omit csv_path; we then fall back to a default repo path.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional, List, Dict
import os
import requests

# Default prod path (used only if csv_path is not provided)
_DEFAULT_CSV = Path("data") / "slip_results.csv"
_FIELDNAMES = ["slip_id", "status", "payout", "updated_at"]


def _in_test_mode() -> bool:
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ


def _fetch_results() -> Optional[List[Dict]]:
    """
    Return a list of result dicts, or None/[] on failure/no data.
    In tests, we keep a tiny timeout so unmocked calls short-circuit quickly.
    The URL is irrelevant for tests (they monkeypatch requests.get).
    """
    try:
        r = requests.get(os.getenv("SLIP_API_URL", "http://localhost/pp-edge/slips"),
                         timeout=0.1 if _in_test_mode() else 5.0)
    except Exception:
        return None
    if getattr(r, "status_code", 0) != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    rows = (data or {}).get("results", [])
    return rows or None


def poll(csv_path: Optional[Path] = None) -> Path:
    """
    Poll and (if rows present) append to csv_path.
    - When rows exist: ensure directory, write header if needed, write rows.
    - When no rows / no network: do nothing (and DO NOT create the file).
    Returns the target path either way.
    """
    target = Path(csv_path) if csv_path is not None else _DEFAULT_CSV

    rows = _fetch_results()
    if not rows:  # honor tests expecting no file on no-network in test-mode
        return target

    # Write/append filtered rows
    target.parent.mkdir(parents=True, exist_ok=True)
    write_header = not target.exists() or target.stat().st_size == 0
    with target.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_FIELDNAMES)
        if write_header:
            w.writeheader()
        filtered = [{k: row.get(k) for k in _FIELDNAMES} for row in rows]
        w.writerows(filtered)
    return target


__all__ = ["poll"]

