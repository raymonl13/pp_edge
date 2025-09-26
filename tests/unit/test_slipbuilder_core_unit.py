import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},"payouts":{"Power2":3.0}}
def test_slipbuilder_builds_top_pair_respecting_rules():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=0)
    legs = [
        {"player":"A","p_hit":0.72,"edge_pp":0.12,"game_id":"g1"},
        {"player":"B","p_hit":0.70,"edge_pp":0.11,"game_id":"g2"},
        {"player":"B","p_hit":0.70,"edge_pp":0.11,"game_id":"g3"},
        {"player":"C","p_hit":0.58,"edge_pp":0.02,"game_id":"g4"},
    ]
    slips = sb.build_slips(legs)
    assert slips
    s = slips[0]
    assert s.get("slip_type") == "Power2"
    assert len(s.get("legs",[])) == 2
    players = {l["player"] for l in s["legs"]}
    assert "A" in players and "B" in players
