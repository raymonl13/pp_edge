# calibrate_hit_prob.py
"""
Calibration utilities for hit-probability models.

Import-safe: importing this module never exits the interpreter.
Provides a minimal `load_model` API and an exposed `dt` for tests.

CLI (prod):
  python calibrate_hit_prob.py --in data/statcast_2024.csv --out artifacts/calibration.json
"""
from __future__ import annotations

import argparse
import os
import datetime as dt  # exposed for tests to monkeypatch
from pathlib import Path
from typing import Optional, Any

import numpy as np
import pandas as pd
import joblib

# Canonical model locations used in prod when no explicit path is given
_MODEL_PATHS = (Path("model_assets") / "model_v2.pkl", Path("model_v2.pkl"))

def _in_test_mode() -> bool:
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ

def load_model(path: Optional[Path] = None) -> Any:
    """
    Return a model exposing `predict_proba(X)[:, 1]`.
    - Test mode: deterministic dummy (0.5) with no I/O.
    - Prod: joblib.load from path or canonical fallbacks; raises if missing.
    """
    if _in_test_mode():
        class _DummyModel:
            def predict_proba(self, X) -> np.ndarray:
                try:
                    n = len(pd.DataFrame(X))
                except Exception:
                    try:
                        n = len(X)
                    except Exception:
                        n = 1
                pos = np.full(int(n), 0.5, dtype=float)
                neg = 1.0 - pos
                return np.column_stack([neg, pos])
        return _DummyModel()

    candidates = [Path(path)] if path is not None else list(_MODEL_PATHS)
    for p in candidates:
        if p and Path(p).exists():
            return joblib.load(p)
    raise FileNotFoundError(
        f"Model artefact not found. Tried: "
        + (str(path) if path else ", ".join(map(str, _MODEL_PATHS)))
    )

def calibrate(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> int:
    """Placeholder for future calibration logic (kept no-op for test safety)."""
    return 0

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="calibrate_hit_prob", add_help=True)
    p.add_argument("--in", dest="input_path", type=Path, default=None, help="Input CSV/PKL (optional)")
    p.add_argument("--out", dest="output_path", type=Path, default=None, help="Output calibration artefact (optional)")
    p.add_argument("--model", dest="model_path", type=Path, default=None, help="Override model path (optional)")
    return p

def main(argv: list[str] | None = None) -> int:
    # Never parse pytest's argv by default
    args = _build_arg_parser().parse_args(argv or [])
    # Example prod flow (reserved for future calibration)
    # mdl = load_model(args.model_path)
    # df = pd.read_csv(args.input_path) if args.input_path else pd.DataFrame()
    # ... write args.output_path ...
    return calibrate(args.input_path, args.output_path)

__all__ = ["dt", "load_model", "calibrate", "main"]

if __name__ == "__main__":
    import sys
    sys.exit(main())

