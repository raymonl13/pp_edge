import os, sys, importlib.util, importlib, inspect, pathlib
import numpy as np, pandas as pd, pytest

pytestmark = pytest.mark.unit

def _load_mc():
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

def _call_simulate(sim, edges, runs=100, seed=42):
    """Call simulate with signature-aware kwargs; adapt if payout/bankroll/unit is required."""
    sig = inspect.signature(sim)
    kw = {}
    if "edges" in sig.parameters: kw["edges"] = edges
    if "runs"  in sig.parameters: kw["runs"]  = runs
    if "seed"  in sig.parameters: kw["seed"]  = seed
    if "unit"  in sig.parameters: kw["unit"]  = 1.0
    if "bankroll" in sig.parameters and "unit" not in sig.parameters:
        kw["bankroll"] = 100.0

    # First attempt
    try:
        return sim(**kw)
    except KeyError as e:
        # If the implementation requires a payout signal, satisfy it and retry once.
        if "payout" in str(e).lower():
            # If payout is expected as a column, add it.
            if "payout" not in edges.columns:
                edges = edges.copy()
                edges["payout"] = 2.0  # minimal, deterministic payout
            # If payout is a kwarg in this signature, pass it too.
            if "payout" in sig.parameters:
                kw["payout"] = 2.0
            return sim(**kw)
        raise

def test_simulate_deterministic_seed():
    mc = _load_mc()
    sim = getattr(mc, "simulate", None)
    if sim is None or not callable(sim):
        pytest.skip("simulate() not available")

    # Minimal deterministic input; add only 'edge' initially (test adapts if more required)
    edges = pd.DataFrame({"edge":[0.05, 0.00, -0.02]})

    r1 = _call_simulate(sim, edges, runs=100, seed=42)
    r2 = _call_simulate(sim, edges, runs=100, seed=42)

    a1, a2 = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    assert len(a1) == 100 == len(a2)
    assert np.allclose(a1, a2)
