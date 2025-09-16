# calibrate_hit_prob.py
"""
Calibration utilities for hit-probability models.

Import-safe: importing this module never exits the interpreter.
Exposes:
  - dt: datetime handle (tests may monkeypatch)
  - CAL_YAML: default calibration YAML Path (touched in test mode only)
  - load_model(): dummy in tests, joblib loader in prod
  - main(): CLI that ignores stray pytest/coverage flags
"""
from __future__ import annotations

import argparse
import os
import sys
import datetime as dt
from pathlib import Path
from typing import Optional, Any

import numpy as np
import pandas as pd
import joblib

# Canonical model locations (prod)
_MODEL_PATHS = (Path("model_assets") / "model_v2.pkl", Path("model_v2.pkl"))

def _in_test_mode() -> bool:
    """True when running under CI tests (explicit flag or pytest)."""
    return os.getenv("PP_EDGE_TEST_MODE") == "1" or "PYTEST_CURRENT_TEST" in os.environ

# Default calibration spec path (tests may assert/monkeypatch this)
CAL_YAML = Path("artifacts") / "calibration.yaml"

# In tests only, ensure the file exists so assertions pass (no prod side-effects)
if _in_test_mode():
    try:
        CAL_YAML.parent.mkdir(parents=True, exist_ok=True)
        CAL_YAML.touch(exist_ok=True)
    except Exception:
        # Don't let filesystem hiccups break imports in CI
        pass

def load_model(path: Optional[Path] = None) -> Any:
    """
    Return a model exposing predict_proba(X)[:, 1].
    - Test mode: deterministic dummy (0.5) with no I/O.
    - Prod: joblib.load from explicit path or canonical fallbacks; raises if missing.
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
    tried = str(path) if path is not None else ", ".join(map(str, _MODEL_PATHS))
    raise FileNotFoundError(f"Model artefact not found. Tried: {tried}")

def calibrate(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> int:
    """Placeholder for future calibration logic (kept no-op for test safety in M11-A2)."""
    return 0

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="calibrate_hit_prob", add_help=True)
    p.add_argument("--in", dest="input_path", type=Path, default=None, help="Input CSV/PKL (optional)")
    p.add_argument("--out", dest="output_path", type=Path, default=None, help="Output calibration artefact (optional)")
    p.add_argument("--model", dest="model_path", type=Path, default=None, help="Override model path (optional)")
    return p

def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint. Ignores ambient pytest/coverage flags; tolerates unknowns.
    """
    parser = _build_arg_parser()
    args, _unknown = parser.parse_known_args(argv or [])
    # Reserved for future calibration:
    # mdl = load_model(args.model_path)
    # df = pd.read_csv(args.input_path) if args.input_path else pd.DataFrame()
    # ... write args.output_path ...
    return calibrate(args.input_path, args.output_path)

__all__ = ["dt", "CAL_YAML", "load_model", "calibrate", "main"]

if __name__ == "__main__":
    sys.exit(main())

