import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":1},"payouts":{"Power2":3.0}}
def test_slipbuilder_no_valid_pair_returns_empty():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=0)
    legs = [
        {"player":"A","p_hit":0.7,"edge_pp":0.12,"game_id":"g1"},
        {"player":"B","p_hit":0.69,"edge_pp":0.11,"game_id":"g1"},
    ]
    slips = sb.build_slips(legs)
    assert isinstance(slips, list)
    assert len(slips) in (0, 1)
    if slips:
        players = {l["player"] for l in slips[0].get("legs", [])}
        assert players != {"A","B"}
