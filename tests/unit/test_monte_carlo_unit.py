import os, sys, importlib.util, importlib, inspect, pathlib
import numpy as np, pytest
try:
    from tests.unit._fixtures import make_edges_df
except Exception:
    from ._fixtures import make_edges_df

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

def test_simulate_deterministic_seed():
    mc  = _load_mc()
    sim = getattr(mc, "simulate", None)
    if sim is None or not callable(sim):
        pytest.skip("simulate() not available")

    edges = make_edges_df(n=3, edge_vals=(0.05, 0.00, -0.02), payout=2.0, win_prob=0.5)

    sig = inspect.signature(sim)
    kwargs = {}
    if "edges" in sig.parameters: kwargs["edges"] = edges
    if "runs"  in sig.parameters: kwargs["runs"]  = 100
    if "seed"  in sig.parameters: kwargs["seed"]  = 42
    if "unit"  in sig.parameters: kwargs["unit"]  = 1.0
    if "bankroll" in sig.parameters and "unit" not in sig.parameters:
        kwargs["bankroll"] = 100.0
    if "payout" in sig.parameters:
        kwargs["payout"] = 2.0
    if "win_prob" in sig.parameters:
        kwargs["win_prob"] = 0.5

    r1 = sim(**kwargs); r2 = sim(**kwargs)
    a1, a2 = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    assert len(a1) == 100 == len(a2)
    assert np.allclose(a1, a2)
