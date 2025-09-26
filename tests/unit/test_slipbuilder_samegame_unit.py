import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":3},"payouts":{"Power2":3.0}}
def test_slipbuilder_avoids_same_game_pairing():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=0)
    legs = [
        {"player":"A","p_hit":0.7,"edge_pp":0.12,"game_id":"g1"},
        {"player":"B","p_hit":0.69,"edge_pp":0.11,"game_id":"g1"},
        {"player":"C","p_hit":0.65,"edge_pp":0.08,"game_id":"g2"},
    ]
    slips = sb.build_slips(legs)
    assert slips
    s = slips[0]
    players = {l["player"] for l in s["legs"]}
    assert not (players == {"A","B"})
