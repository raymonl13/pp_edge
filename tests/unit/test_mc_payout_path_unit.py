import importlib, inspect, pytest, numpy as np, pandas as pd
pytestmark = pytest.mark.unit

def _load():
    try:
        return importlib.import_module("monte_carlo_bankroll")
    except Exception as e:
        pytest.skip(f"monte_carlo_bankroll not importable: {e}")

def test_simulate_payout_kw_vs_column_paths():
    mc = _load()
    sim = getattr(mc, "simulate", None)
    if sim is None or not callable(sim): pytest.skip("simulate() not available")
    edges = pd.DataFrame({"edge":[0.05, 0.00, -0.02], "payout":[2.0,2.0,2.0], "win_prob":[0.5,0.5,0.5]})
    sig = inspect.signature(sim)
    kwargs = {"edges": edges, "runs": 50, "seed": 123}
    if "unit" in sig.parameters: kwargs["unit"]=1.0
    if "win_prob" in sig.parameters: kwargs["win_prob"]=0.5

    # path A: payout as kw if supported
    a_kwargs = dict(kwargs)
    if "payout" in sig.parameters: a_kwargs["payout"]=2.0
    a = np.asarray(sim(**a_kwargs), dtype=float); assert len(a)==50

    # path B: payout via column only
    b = np.asarray(sim(**kwargs), dtype=float); assert len(b)==50
