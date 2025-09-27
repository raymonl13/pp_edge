import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder=None
def test_no_build_when_insufficient_legs():
    if SlipBuilder is None: pytest.skip("SlipBuilder seam absent")
    cfg={"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":1},"payouts":{"Power2":3.0}}
    sb=SlipBuilder(cfg)
    slips=sb.build_slips([{"player":"A","game_id":"g1","p_hit":0.6,"edge_pp":0.1}])
    assert slips==[] or all(len(s.get("legs",[]))>=2 for s in slips)
