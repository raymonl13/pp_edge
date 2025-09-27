import numpy as np, pandas as pd, pytest
try:
    from monte_carlo_bankroll import simulate
except Exception:
    simulate = None

pytestmark = pytest.mark.unit

def test_simulate_seed_changes_outcome_and_mean_is_reasonable():
    if simulate is None:
        pytest.skip("simulate seam absent")
    edges = pd.DataFrame({"payout":[2.0, 3.0, 1.5], "win_prob":[0.52, 0.50, 0.48]})
    a = np.asarray(simulate(edges=edges, unit=1.0, runs=256, seed=7), dtype=float)
    b = np.asarray(simulate(edges=edges, unit=1.0, runs=256, seed=11), dtype=float)
    assert a.shape == (256,) and b.shape == (256,)
    assert not np.allclose(a, b)
    for arr in (a, b):
        assert float(np.var(arr)) > 0.0
        m = float(np.mean(arr))
        assert -1.0 <= m <= 2.0
