# poll_slip_results.py
"""
Polling utility for slip results.

Contract (tests):
- ps.poll(csv_path) SHOULD create/write the CSV at csv_path when GET returns rows.
- In test mode without network stubs (or non-200), it should NOT create the file.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Optional, List, Dict
import requests

_DEFAULT_CSV = Path("data") / "slip_results.csv"
_FIELDNAMES = ["slip_id", "status", "payout", "updated_at"]


def _in_test_mode() -> bool:
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ


def _fetch_results() -> Optional[List[Dict]]:
    """Return list of result dicts, or None on failure/no data."""
    try:
        r = requests.get(
            os.getenv("SLIP_API_URL", "http://localhost/pp-edge/slips"),
            timeout=0.1 if _in_test_mode() else 5.0,
        )
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
    Poll and (if rows present) write to csv_path.
    - When rows exist: guarantee the file is created and rows are appended.
    - When no rows / no network: do nothing; DO NOT create a file.
    Returns the path either way (tests assert existence only when rows are present).
    """
    target = Path(csv_path) if csv_path is not None else _DEFAULT_CSV
    rows = _fetch_results()
    if not rows:
        return target  # honour “no file on no-network” test

    # Ensure dir exists and file will exist on rows
    target.parent.mkdir(parents=True, exist_ok=True)
    write_header = not target.exists() or target.stat().st_size == 0
    if not target.exists():
        target.touch(exist_ok=True)

    with target.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_FIELDNAMES)
        if write_header:
            w.writeheader()
        filtered = [{k: row.get(k) for k in _FIELDNAMES} for row in rows]
        if filtered:
            w.writerows(filtered)

    return target


__all__ = ["poll"]

