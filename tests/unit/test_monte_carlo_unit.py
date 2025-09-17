import os, sys, importlib.util, importlib, inspect, pathlib
import numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit

def _load_mc_module():
    try:
        return importlib.import_module("monte_carlo_bankroll")
    except ModuleNotFoundError:
        root = pathlib.Path(__file__).resolve().parents[2]
        for p in (root / "monte_carlo_bankroll.py", root / "scripts" / "monte_carlo_bankroll.py"):
            if p.exists():
                spec = importlib.util.spec_from_file_location("monte_carlo_bankroll", str(p))
                mod = importlib.util.module_from_spec(spec)
                sys.modules["monte_carlo_bankroll"] = mod
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                return mod
        pytest.skip("monte_carlo_bankroll module not found")

def test_simulate_deterministic_seed():
    mc = _load_mc_module()
    sim = getattr(mc, "simulate", None)
    if sim is None or not callable(sim):
        pytest.skip("simulate() not available on monte_carlo_bankroll")

    edges = pd.DataFrame({"edge":[0.05, 0.00, -0.02]})
    sig = inspect.signature(sim)
    kwargs = {}
    if "edges" in sig.parameters: kwargs["edges"] = edges
    if "runs"  in sig.parameters: kwargs["runs"]  = 100
    if "seed"  in sig.parameters: kwargs["seed"]  = 42
    if "unit"  in sig.parameters: kwargs["unit"]  = 1.0
    if "bankroll" in sig.parameters and "unit" not in sig.parameters:
        kwargs["bankroll"] = 100.0

    r1 = sim(**kwargs)
    r2 = sim(**kwargs)
    assert hasattr(r1, "__len__") and len(r1) == len(r2)
    assert np.allclose(np.asarray(r1, dtype=float), np.asarray(r2, dtype=float))
