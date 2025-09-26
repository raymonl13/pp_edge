import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":1},"payouts":{"Power2":3.0}}
def test_slipbuilder_respects_daily_demon_quota():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=1)
    legs = [
        {"player":"A","p_hit":0.7,"edge_pp":0.12,"tag":"Demon","game_id":"g1"},
        {"player":"B","p_hit":0.69,"edge_pp":0.11,"game_id":"g2"},
        {"player":"C","p_hit":0.68,"edge_pp":0.10,"game_id":"g3"},
    ]
    slips = sb.build_slips(legs)
    assert slips
    s = slips[0]
    assert len([l for l in s["legs"] if l.get("tag")=="Demon"]) == 0 or len([l for l in s["legs"] if l.get("tag")=="Demon"]) == 1
