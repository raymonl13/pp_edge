# run_edge_sheet.py
"""
Import-safe runner for the edge sheet.

- NEVER exits at import time.
- When executed as a script, it:
    * accepts --date YYYY-MM-DD (default today)
    * skips cleanly (exit code 0) if the model artefact is missing
    * otherwise defers to code_cli_run_edge_sheet_v1.py
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
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="run_edge_sheet", add_help=True)
    p.add_argument("--date", dest="run_date", default=str(date.today()))
    args = p.parse_args(argv or [])

    # Skip cleanly if model is missing (unit test invariant + nightly skip behaviour)
    if not MODEL_PATH.exists():
        print("[nightly_edge_sheet] Missing model; skipping.", flush=True)
        return 0

    # Defer to canonical CLI for generation (keeps behaviour single-sourced)
    cmd = [sys.executable, "code_cli_run_edge_sheet_v1.py", "--date", args.run_date]
    return int(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    sys.exit(main())

