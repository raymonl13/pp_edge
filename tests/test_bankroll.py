from code_utils_bankroll_v2 import allocate_stakes

_CFG = {
    "unit_pct": 0.02,
    "limits": {"demon_pct": 0.1, "goblin_pct": 0.15},
}

def _slip(tag=None):
    leg = {"player": "P", "p_hit": 0.7}
    if tag:
        leg["tag"] = tag
    return {"slip_type": "Power2", "legs": [leg], "edge_pp": 0.1}

def test_caps_respected():
    slips = [_slip("Demon") for _ in range(10)] + [_slip("Goblin") for _ in range(10)] + [_slip() for _ in range(10)]
    allocated, remaining = allocate_stakes(slips, 1000.0, _CFG)
    demon_stake = sum(s["stake_total"] for s in allocated if any(l.get("tag") == "Demon" for l in s["legs"]))
    goblin_stake = sum(s["stake_total"] for s in allocated if any(l.get("tag") == "Goblin" for l in s["legs"]))
    assert demon_stake <= 1000.0 * _CFG["limits"]["demon_pct"]
    assert goblin_stake <= 1000.0 * _CFG["limits"]["goblin_pct"]
