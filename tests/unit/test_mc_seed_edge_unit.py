import numpy as np, pandas as pd
from monte_carlo_bankroll import simulate
def test_simulate_runs_eq_1_shape_and_determinism():
    edges = pd.DataFrame({"payout":[2.0,3.0], "win_prob":[0.5,1.0]})
    a = simulate(edges=edges, unit=1.0, runs=1, seed=7)
    b = simulate(edges=edges, unit=1.0, runs=1, seed=7)
    assert np.shape(a) == (1,)
    assert np.allclose(a, b)
