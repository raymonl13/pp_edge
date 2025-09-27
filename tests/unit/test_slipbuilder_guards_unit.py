import pytest
REQUIRED_KEYS = {"player","game_id","p_hit","edge_pp"}

try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None

pytestmark = pytest.mark.unit

def test_emitted_slips_respect_leg_count_and_contract_keys():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder seam absent")
    cfg = {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},
           "payouts":{"Power2":3.0,"Power3":5.0}}
    legs = [
        {"player":"A","game_id":"g1","p_hit":0.6,"edge_pp":0.1},
        {"player":"B","game_id":"g2","p_hit":0.62,"edge_pp":0.12},
        {"player":"C","game_id":"g3","p_hit":0.58,"edge_pp":0.09},
        {"player":"D","game_id":"g4","p_hit":0.55,"edge_pp":0.08},
        {"player":"E","game_id":"g5","p_hit":0.57,"edge_pp":0.11},
        {"player":"F","game_id":"g6","p_hit":0.59,"edge_pp":0.10},
    ]
    sb = SlipBuilder(cfg)
    slips = sb.build_slips(legs)
    assert isinstance(slips, list)
    for s in slips:
        l = s.get("legs", [])
        assert 2 <= len(l) <= 6
        for leg in l:
            assert REQUIRED_KEYS.issubset(leg.keys())
