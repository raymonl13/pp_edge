import sys, pathlib
sys.path.append(pathlib.Path(__file__).resolve().parents[1].as_posix())

from code_utils_slipbuilder_v2 import SlipBuilder
from code_utils_bankroll_v2 import allocate_stakes

cfg_builder = {"diversification": {"demon_quota_per_slip": 1, "demon_quota_per_day": 6},
               "payouts": {"Power2": 3, "Power3": 5}}
legs = [{"player": f"P{i}", "p_hit": 0.72, "edge_pp": 0.12,
         "tag": ("Demon" if i == 0 else "Goblin" if i == 1 else None)} for i in range(8)]
slips = SlipBuilder(cfg_builder).build_slips(legs)

cfg_bankroll = {"unit_pct": 0.02,
                "limits": {"demon_pct": 0.10, "goblin_pct": 0.15}}
slips, remaining = allocate_stakes(slips, 1000.0, cfg_bankroll)

for s in slips:
    print(s["slip_type"], s["stake_total"])
print("Remaining:", remaining)
