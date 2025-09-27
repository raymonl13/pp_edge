import os
os.environ["PP_EDGE_TEST_MODE"]="1"

import importlib, inspect, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit

def _get_sim():
    for mod in ("monte_carlo_bankroll","monte_carlo","mc"):
        try:
            m = importlib.import_module(mod)
            fn = getattr(m, "simulate", None)
            if callable(fn):
                return fn
        except Exception:
            continue
    return None

def test_mc_alt_payout_schedule_deterministic():
    sim = _get_sim()
    if sim is None:
        pytest.skip("simulate() not exposed in this build")
    sig = inspect.signature(sim)

    edges = pd.DataFrame({
        "payout":   [2.0, 3.0, 1.5, 2.25],
        "win_prob": [0.0, 1.0, 0.5, 0.55]
    })

    args = {}
    for k,v in {"edges":edges,"unit":1.0,"runs":256,"seed":11,"payout":2.0,"win_prob":0.55}.items():
        if k in sig.parameters:
            args[k]=v

    r1 = np.asarray(sim(**args), dtype=float)
    r2 = np.asarray(sim(**args), dtype=float)

    assert r1.shape == (256,)
    assert np.allclose(r1, r2)

    sure = pd.DataFrame({"payout":[3.0],"win_prob":[1.0]})
    args2 = dict(args)
    if "edges" in sig.parameters: args2["edges"]=sure
    if "runs" in sig.parameters:  args2["runs"]=32
    if "seed" in sig.parameters:  args2["seed"]=7
    r3 = np.asarray(sim(**args2), dtype=float)
    assert np.allclose(r3, np.full(32, 3.0-1.0))
