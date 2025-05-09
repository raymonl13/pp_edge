"""
PP-EDGE v6.7 | Milestone M3 – Edge Plumbing
(bankroll sizing deferred to M5)
"""
# — try real helper, fall back to stub —
try:
    from code_utils_prob_v1 import bayes_hit_prob
except ImportError:                       # helper not found → safe stub
    def bayes_hit_prob(leg): return 0.5

# — edge calc —
def calc_edge(p_hit, payout, num_legs):
    ev = (p_hit ** num_legs) * payout
    return ev - 1

# — engine —
def run_engine(legs, *, num_legs, payout, slip_type="Power"):
    out = []
    for leg in legs:
        p = bayes_hit_prob(leg)
        out.append({**leg,
                    "p_hit":   round(p,4),
                    "edge_pp": round(calc_edge(p, payout, num_legs),4),
                    "stake":   None})          # TODO Milestone M5
    return out
