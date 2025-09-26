import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None
pytestmark = pytest.mark.unit
def _cfg():
    return {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},"payouts":{"Power2":3.0}}
def test_slipbuilder_quotas_and_same_game():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder not available")
    sb = SlipBuilder(_cfg(), demons_used_today=1)
    legs = [
        {"player":"A","p_hit":0.66,"edge_pp":0.10,"tag":"Demon","game_id":"g1"},
        {"player":"B","p_hit":0.66,"edge_pp":0.09,"game_id":"g1"},
        {"player":"C","p_hit":0.66,"edge_pp":0.08,"game_id":"g2"},
        {"player":"C","p_hit":0.66,"edge_pp":0.08,"game_id":"g3"},
    ]
    slips = sb.build_slips(legs)
    assert slips
    s = slips[0]
    assert s["slip_type"] == "Power2"
    assert len(s["legs"]) == 2
    players = {l["player"] for l in s["legs"]}
    assert "C" in players
    assert not (players == {"A","B"})
    demons = [l for l in s["legs"] if l.get("tag")=="Demon"]
    assert len(demons) <= 1
