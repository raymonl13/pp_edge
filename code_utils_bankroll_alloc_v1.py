from typing import List, Dict

def allocate_slips(
    slips: List[Dict],
    bankroll: float = 100.0,
    slip_cap: float = 2.0,
    slate_cap_frac: float = 0.10,
    kelly: float = 0.5,
    min_stake: float = 0.0,
    allow_neg_ev: bool = False,
) -> List[Dict]:
    """
    Kelly-lite allocator:
      stake_i = min(slip_cap, bankroll * kelly * max(edge_pp_i, 0))
    Enforce slate budget: budget = min(bankroll * slate_cap_frac, bankroll)
    Filter negatives unless allow_neg_ev=True. Returns slips with stake_total set.
    """
    # filter + sort by descending edge
    cand = []
    for s in slips:
        edge = float(s.get("edge_pp", 0.0) or 0.0)
        if edge <= 0.0 and not allow_neg_ev:
            continue
        cand.append(s)
    cand.sort(key=lambda s: float(s.get("edge_pp", 0.0) or 0.0), reverse=True)

    budget = min(bankroll * slate_cap_frac, bankroll)
    out = []
    for s in cand:
        if budget < max(1e-12, min_stake):
            break
        edge = float(s.get("edge_pp", 0.0) or 0.0)
        eff_edge = max(edge, 0.0)
        raw = bankroll * kelly * eff_edge
        stake = min(slip_cap, raw)
        # clip to remaining budget
        stake = min(stake, budget)
        # prune tiny stakes
        if stake < min_stake:
            continue
        s = dict(s)  # shallow copy so we don't mutate caller
        s["stake_total"] = round(float(stake), 4)
        out.append(s)
        budget -= stake
    return out
