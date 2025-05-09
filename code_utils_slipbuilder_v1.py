"""
SlipBuilder v1 · PP-EDGE Milestone 4
Builds slips that respect diversification / quota rules.
"""

from typing import List, Dict, Any
from itertools import combinations

class SlipBuilder:
    def __init__(self, cfg: Dict[str, Any], *, demons_used_today: int = 0):
        self.cfg   = cfg
        self.div   = cfg["diversification"]
        self.pouts = cfg["payouts"]
        self.demons_used_today = demons_used_today

    # ---------- public API ----------
    def build_slips(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Greedy builder: fill Power4, then Power6, then Flex6."""
        slips, pool = [], sorted(legs, key=lambda x: x["edge_pp"], reverse=True)
        while True:
            made = False
            for slip_type, n_legs in [("Power4", 4), ("Power6", 6)]:
                slip = self._try_make(pool, slip_type, n_legs)
                if slip:
                    slips.append(slip)
                    pool = [l for l in pool if l not in slip["legs"]]
                    made = True
                    break
            if not made:
                break
        return slips

    # ---------- internals ----------
    def _try_make(self, pool, slip_type, n_legs):
        if len(pool) < n_legs:
            return None
        for combo in combinations(pool, n_legs):
            if self._valid(combo):
                return {
                    "slip_type":  slip_type,
                    "legs":       list(combo),
                    "edge_pp":    round(self._slip_edge(combo, slip_type), 4),
                    "stake_total": None,          # M5 will fill
                }
        return None

    def _valid(self, combo):
        # no duplicate players
        if len({l["player"] for l in combo}) < len(combo):
            return False
        # demon quotas
        demons = [l for l in combo if l.get("tag") == "Demon"]
        if len(demons) > self.div["demon_quota_per_slip"]:
            return False
        if self.demons_used_today + len(demons) > self.div["demon_quota_per_day"]:
            return False
        # same-game cap 1
        games = [l.get("game_id") for l in combo if l.get("game_id")]
        if len(games) != len(set(games)):
            return False
        return True

    def _slip_edge(self, combo, slip_type):
        p = 1.0
        for leg in combo:
            p *= leg["p_hit"]
        return (p * self.pouts[slip_type]) - 1.0
