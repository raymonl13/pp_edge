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
def _call(sim, edges, runs=128, seed=11, as_kwargs=False):
    sig = inspect.signature(sim)
    if as_kwargs:
        kw = {}
        for k,v in {"edges":edges,"runs":runs,"seed":seed,"unit":1.0,"payout":2.5,"win_prob":0.57}.items():
            if k in sig.parameters:
                kw[k] = v
        return sim(**kw)
    return sim(edges, runs) if len(sig.parameters) < 3 else sim(edges=edges, runs=runs, seed=seed)
def test_mc_payout_path_deterministic():
    sim = _find_sim()
    if sim is None:
        pytest.skip("simulate() not available")
    edges = pd.DataFrame({"edge":[0.02,0.01,0.00,-0.01], "payout":[2.5]*4, "win_prob":[0.57,0.53,0.50,0.47]})
    r1 = np.asarray(_call(sim, edges, runs=128, seed=11, as_kwargs=True), dtype=float)
    r2 = np.asarray(_call(sim, edges, runs=128, seed=11, as_kwargs=True), dtype=float)
    assert len(r1) == 128 == len(r2)
    assert np.allclose(r1, r2)
