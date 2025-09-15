# calibrate_hit_prob.py
"""
Calibration utility for hit-probability models.

Import-safe: this module performs **no** process termination at import time.
Run from CLI to execute calibration; importing this module in tests is safe.

Usage (examples):
  python calibrate_hit_prob.py
  python calibrate_hit_prob.py --in data/statcast_2024.csv --out artifacts/calibration.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional


def calibrate(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> int:
    """
    Placeholder calibration routine.

    In production you can replace the internals with real calibration logic
    (isotonic/logistic calibration, reliability plots, etc.). For now this
    function is intentionally no-op and returns 0 so tests importing this
    module don't exit prematurely.
    """
    # Intentionally no side effects here for test safety.
    # Implement real calibration here when ready.
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="calibrate_hit_prob", add_help=True)
    p.add_argument("--in", dest="input_path", type=Path, default=None, help="Path to input CSV/PKL (optional)")
    p.add_argument("--out", dest="output_path", type=Path, default=None, help="Path to write calibration artefact (optional)")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Delegate to the calibrate routine (currently a no-op returning 0).
    return calibrate(args.input_path, args.output_path)


__all__ = ["calibrate", "main"]


if __name__ == "__main__":
    # Only exit the interpreter when *executed* as a script, never on import.
    import sys

    sys.exit(main())

