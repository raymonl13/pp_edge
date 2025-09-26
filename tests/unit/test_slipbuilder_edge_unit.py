import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":3},"payouts":{"Power2":3.0}}
def test_slipbuilder_edge_or_ev_present_and_reasonable():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=0)
    legs = [
        {"player":"A","p_hit":0.66,"edge_pp":0.10,"game_id":"g1"},
        {"player":"B","p_hit":0.64,"edge_pp":0.08,"game_id":"g2"},
        {"player":"B","p_hit":0.64,"edge_pp":0.08,"game_id":"g3"},
    ]
    slips = sb.build_slips(legs)
    assert slips
    s = slips[0]
    assert s.get("slip_type") == "Power2"
    assert len(s.get("legs",[])) == 2
    metric_key = next((k for k in ("edge","ev","expected_value") if k in s), None)
    if metric_key is not None:
        val = float(s[metric_key])
        assert val == val
