import importlib, inspect, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
def _find_sim():
    for modname in ("monte_carlo_bankroll","monte_carlo","mc"):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        sim = getattr(mod, "simulate", None)
        if callable(sim):
            return sim
    return None
def _call_sim(sim, edges, runs=128, seed=7):
    sig = inspect.signature(sim)
    kw = {}
    defaults = {"edges":edges, "runs":runs, "seed":seed, "unit":1.0, "payout":2.0, "win_prob":0.55}
    for name in ("edges","runs","seed","unit","payout","win_prob"):
        if name in sig.parameters:
            kw[name] = defaults[name]
    return sim(**kw)
def test_simulate_deterministic_seed():
    sim = _find_sim()
    if sim is None:
        pytest.skip("simulate() not available")
    edges = pd.DataFrame({"edge":[0.03,0.00,-0.01,0.05], "payout":[2.0]*4, "win_prob":[0.54,0.50,0.49,0.58]})
    r1 = np.asarray(_call_sim(sim, edges, runs=128, seed=7), dtype=float)
    r2 = np.asarray(_call_sim(sim, edges, runs=128, seed=7), dtype=float)
    assert len(r1) == 128 == len(r2)
    assert np.allclose(r1, r2)
