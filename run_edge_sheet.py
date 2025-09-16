# run_edge_sheet.py
"""
Import-safe runner for the edge sheet.

- NEVER exits at import time.
- When executed as a script, it:
    * optionally accepts --date YYYY-MM-DD
    * skips cleanly (exit 0) if the model artefact is missing
    * otherwise defers to the canonical CLI: code_cli_run_edge_sheet_v1.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

MODEL_PATH = Path("model_assets/model_v2.pkl")


def _in_test_mode() -> bool:
    # Unit tests set this; nightly/workflows should be strict but skip cleanly.
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ


def main(argv: list[str] | None = None) -> int:
    # Parse args (keep minimal to avoid surprises)
    parser = argparse.ArgumentParser(prog="run_edge_sheet", add_help=True)
    parser.add_argument("--date", dest="run_date", default=str(date.today()), help="ISO date (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    # Skip cleanly if model is missing (tests and nightly expect this to be 0)
    if not MODEL_PATH.exists():
        print("[nightly_edge_sheet] Missing model; skipping.", flush=True)
        return 0

    # Defer to the canonical CLI instead of duplicating logic here
    cmd = [sys.executable, "code_cli_run_edge_sheet_v1.py", "--date", args.run_date]
    proc = subprocess.run(cmd)
    return int(proc.returncode)


if __name__ == "__main__":
    sys.exit(main())

