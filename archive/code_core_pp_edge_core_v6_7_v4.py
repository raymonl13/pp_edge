"""
PP-EDGE v6.7 | Milestone 4 – Diversification & Quotas
• Prices Power-style legs (skip Flex6 for now)
• Builds slips via SlipBuilder
"""

from typing import List, Dict, Any
import yaml, pathlib

# --- helper import ---------------------------------------------------------
try:
    from code_utils_prob_v1 import bayes_hit_prob      # ≥ M2
except ImportError:
    def bayes_hit_prob(leg): return 0.5                # stub

from code_utils_slipbuilder_v1 import SlipBuilder

# --- math helpers ----------------------------------------------------------
def calc_edge(p_hit: float, payout: float, n: int) -> float:
    return (p_hit ** n) * payout - 1

def _price(raw: List[Dict[str, Any]], payout: float, n: int) -> List[Dict[str, Any]]:
    out = []
    for leg in raw:
        p = bayes_hit_prob(leg)
        out.append({**leg,
                    "p_hit":  round(p, 4),
                    "edge_pp": round(calc_edge(p, payout, n), 4)})
    return out

# --- main pipeline ---------------------------------------------------------
def run_pipeline(raw_legs: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    priced: List[Dict[str, Any]] = []

    # --- NEW: skip Flex6 dict payout until M6 ---
    for slip_type, payout in cfg["payouts"].items():
        if not isinstance(payout, (int, float)):       # Flex6 is a dict → skip
            continue
        n = int(slip_type[-1])                         # Power4 → 4
        priced.extend(_price(raw_legs, payout, n))

    slips = SlipBuilder(cfg).build_slips(priced)
    return slips

# --- smoke-test hook -------------------------------------------------------
if __name__ == "__main__":
    import json, pprint
    ROOT = pathlib.Path(__file__).parent
    with (ROOT / "config_pp_edge_v6.8.yaml").open() as f:
        cfg = yaml.safe_load(f)
    with (ROOT / "data_feed_sample.json").open() as f:
        raw = json.load(f)["projections"]

    pprint.pp(run_pipeline(raw, cfg)[:2])
