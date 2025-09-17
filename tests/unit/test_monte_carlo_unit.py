import numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit

def test_simulate_deterministic_seed():
    import monte_carlo_bankroll as mc
    edges = pd.DataFrame({"edge":[0.05, 0.00, -0.02]})
    r1 = mc.simulate(edges=edges, runs=100, seed=42)
    r2 = mc.simulate(edges=edges, runs=100, seed=42)
    assert hasattr(r1, "__len__") and len(r1) == 100
    assert np.allclose(np.array(r1), np.array(r2))
