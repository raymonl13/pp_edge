from code_utils_model_v1 import predict_hit_prob
"""
PP-EDGE Core v6.7 · Milestone 5
price → filter by edge → build slips → Kelly sizing
"""
from code_utils_prob_v1 import bayes_hit_prob
from code_utils_slipbuilder_v1 import SlipBuilder
from code_utils_bankroll_v1 import size_bet

def _price(raw_legs, payout):
    out = []
    for leg in raw_legs:
        p = bayes_hit_prob(leg)
        edge = round(p * payout - 1.0, 4)
        out.append({**leg, "p_hit": round(p,4), "edge_pp": edge})
    return out

def run_pipeline(raw_legs, cfg):
    payouts = cfg["payouts"]
    # Inject model-based hit probability
    all_priced = []
    for slip_type, payout in [("Power4", payouts["Power4"]), ("Power6", payouts["Power6"])]:
        for leg in _price(raw_legs, payout):
            leg["slip_type"] = slip_type
            all_priced.append(leg)
    # apply edge threshold early
    min_edge = cfg.get("filters", {}).get("min_edge", 0.0)
    priced = [l for l in all_priced if l["edge_pp"] >= min_edge]
    print(f"→ {len(priced)} legs with edge ≥ {min_edge}")
    slips = SlipBuilder(cfg).build_slips(priced)
    state = {"staked_today": 0.0}
    for slip in slips:
        slip["stake_total"] = size_bet(slip["edge_pp"], cfg["bankroll"], state)
    # Inject model-based hit probability
    return slips