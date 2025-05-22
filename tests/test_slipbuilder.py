import random
from code_utils_slipbuilder_v2 import SlipBuilder
_CFG = {
    "diversification": {"demon_quota_per_slip": 1, "demon_quota_per_day": 6},
    "payouts": {
        "Power2": 3.0, "Power3": 5.0, "Power4": 10.0, "Power6": 37.5,
        "Flex4": {"four_correct": 2.0, "three_correct": 0.5},
        "Flex5": {"five_correct": 10.0, "four_correct": 2.0},
        "Flex6": {"six_correct": 25.0, "five_correct": 2.0, "four_correct": 0.4}
    }
}
def _leg(i): 
    return {"player": f"P{i}", "p_hit": 0.7,
            "edge_pp": round(random.uniform(0.05, 0.15), 4)}
def test_slips_exist():
    assert SlipBuilder(_CFG).build_slips([_leg(i) for i in range(8)])
def test_unique_players_per_slip():
    for s in SlipBuilder(_CFG).build_slips([_leg(i) for i in range(10)]):
        p = [l["player"] for l in s["legs"]]
        assert len(p) == len(set(p))
