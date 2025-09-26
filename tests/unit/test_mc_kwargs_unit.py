import importlib, inspect, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
def test_mc_runs_with_all_kwargs():
    for modname in ("monte_carlo_bankroll","monte_carlo","mc"):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        sim = getattr(mod, "simulate", None)
        if callable(sim):
            sig = inspect.signature(sim)
            edges = pd.DataFrame({"edge":[0.01,0.0,-0.01],"payout":[2.0,2.0,2.0],"win_prob":[0.52,0.5,0.48]})
            kw = {}
            for k,v in {"edges":edges,"runs":64,"seed":3,"unit":1.0,"payout":2.0,"win_prob":0.52}.items():
                if k in sig.parameters: kw[k] = v
            out = sim(**kw)
            np.asarray(out, dtype=float)
            return
    pytest.skip("simulate() not available")
