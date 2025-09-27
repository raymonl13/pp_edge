import pytest
from code_utils_bankroll_alloc_v1 import allocate_slips
pytestmark = pytest.mark.unit

def test_allocator_caps_and_budget():
    slips = [
        {"edge_pp": 0.15, "legs":[{"game_id":"g1"}]},
        {"edge_pp": 0.05, "legs":[{"game_id":"g2"}]},
        {"edge_pp": -0.01, "legs":[{"game_id":"g3"}]},
    ]
    out = allocate_slips(slips, bankroll=100.0, slip_cap=2.0, slate_cap_frac=0.05, kelly=0.5)
    # slate budget = 5.0; with caps expect 2.0 + 2.0 <= 5.0; negatives filtered
    assert 1 <= len(out) <= 2
    tot = sum(s["stake_total"] for s in out)
    assert tot <= 5.0 + 1e-9
    assert all(s["stake_total"] <= 2.0 + 1e-9 for s in out)
    assert all(s.get("edge_pp",0) >= 0 for s in out)
