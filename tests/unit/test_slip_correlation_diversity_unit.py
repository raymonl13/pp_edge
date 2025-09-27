import pytest
from code_utils_slipqa_v1 import qa_slip, HARD_FLAGS
pytestmark = pytest.mark.unit
CFG={"diversification":{"demon_quota_per_slip":1}}
def test_low_diversity_and_duplicate_player_flags_soft():
    slip={"edge_pp":0.12,"legs":[{"player":"A","game_id":"g1"},{"player":"A","game_id":"g1"},{"player":"B","game_id":"g1"}]}
    flags=qa_slip(slip,CFG)
    assert flags["low_diversity_games"] and flags["duplicate_player"]
    assert not any(flags.get(k,False) for k in HARD_FLAGS)
def test_correlated_group_soft_flag():
    slip={"edge_pp":0.10,"legs":[{"player":"C","game_id":"g2","correlation_group":"T1"},{"player":"D","game_id":"g3","correlation_group":"T1"},{"player":"E","game_id":"g4","correlation_group":"T2"}]}
    flags=qa_slip(slip,CFG)
    assert flags["correlated_group"]
    assert not any(flags.get(k,False) for k in HARD_FLAGS)
