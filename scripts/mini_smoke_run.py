import sys, pathlib
sys.path.append(pathlib.Path(__file__).resolve().parents[1].as_posix())
from code_utils_slipbuilder_v2 import SlipBuilder
cfg = {"diversification": {"demon_quota_per_slip": 1, "demon_quota_per_day": 6},
       "payouts": {"Power2": 3, "Power3": 5, "Power4": 10, "Power6": 37.5}}
legs = [{"player": f"P{i}", "p_hit": 0.72, "edge_pp": 0.12} for i in range(8)]
for s in SlipBuilder(cfg).build_slips(legs):
    print(s["slip_type"], len(s["legs"]), s["edge_pp"])
