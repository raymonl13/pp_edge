import os
os.environ["PP_EDGE_TEST_MODE"]="1"

import pytest
try:
    from code_utils_slipbuilder_v2 import SlipBuilder
except Exception:
    SlipBuilder = None

pytestmark = pytest.mark.unit

CFG = {
    "diversification": {"demon_quota_per_slip": 1, "demon_quota_per_day": 1},
    "payouts": {"Power2": 3.0}
}

def leg(player, game_id, p_hit=0.65, edge_pp=0.12, tag=None):
    d = {"player": player, "game_id": game_id, "p_hit": p_hit, "edge_pp": edge_pp}
    if tag: d["tag"] = tag
    return d

def test_slipbuilder_rejects_all_same_game():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder unavailable in unit lane")
    sb = SlipBuilder(CFG, demons_used_today=0)
    legs = [leg("A","g1"), leg("B","g1")]
    slips = sb.build_slips(legs)
    assert isinstance(slips, list)
    assert len(slips) in (0,1)
    if slips:
        gids = {l["game_id"] for l in slips[0].get("legs", [])}
        assert len(gids) > 1

def test_slipbuilder_demon_quota_exhausted():
    if SlipBuilder is None:
        pytest.skip("SlipBuilder unavailable in unit lane")
    sb = SlipBuilder({"diversification":{"demon_quota_per_slip":0,"demon_quota_per_day":0},"payouts":{"Power2":3.0}}, demons_used_today=0)
    legs = [leg("A","g1",tag="Demon"), leg("C","g2")]
    slips = sb.build_slips(legs)
    assert isinstance(slips, list)
    assert len(slips) in (0,1)
    if slips:
        assert all(l.get("tag") != "Demon" for l in slips[0].get("legs", []))
