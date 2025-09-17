import os, sys, importlib.util, importlib, pathlib
import numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit

def _load_monte_carlo():
    # First try normal import (works if PYTHONPATH is set correctly)
    try:
        return importlib.import_module("monte_carlo_bankroll")
    except ModuleNotFoundError:
        pass
    # Fallback: load from known file locations
    root = pathlib.Path(__file__).resolve().parents[2]
    candidates = [
        root / "monte_carlo_bankroll.py",
        root / "scripts" / "monte_carlo_bankroll.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("monte_carlo_bankroll", str(path))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["monte_carlo_bankroll"] = mod
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
    pytest.skip("monte_carlo_bankroll not found in repo root or scripts/")

def test_simulate_deterministic_seed():
    mc = _load_monte_carlo()
    edges = pd.DataFrame({"edge":[0.05, 0.00, -0.02]})
    r1 = mc.simulate(edges=edges, runs=100, seed=42)
    r2 = mc.simulate(edges=edges, runs=100, seed=42)
    assert hasattr(r1, "__len__") and len(r1) == 100
    assert np.allclose(np.array(r1), np.array(r2))
