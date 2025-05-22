from itertools import combinations
from math import prod
from typing import Any, Dict, List, Tuple

class SlipBuilder:
    _ORDER: Tuple[Tuple[str, int], ...] = (
        ("Power6", 6), ("Power4", 4), ("Power3", 3), ("Power2", 2),
        ("Flex6", 6), ("Flex5", 5), ("Flex4", 4)
    )
    def __init__(self, cfg: Dict[str, Any], *, demons_used_today: int = 0):
        self.div = cfg["diversification"]
        self.pouts = cfg["payouts"]
        self.demons_used_today = demons_used_today
        self._active = [p for p in self._ORDER if p[0] in self.pouts]
    def build_slips(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        slips, pool = [], sorted(legs, key=lambda l: l["edge_pp"], reverse=True)
        while True:
            made = False
            for s_type, n in self._active:
                slip = self._try_make(pool, s_type, n)
                if slip:
                    slips.append(slip)
                    pool = [l for l in pool if l not in slip["legs"]]
                    made = True
                    break
            if not made:
                break
        return slips
    def _try_make(self, pool: List[Dict[str, Any]], s_type: str, n: int):
        if len(pool) < n:
            return None
        for combo in combinations(pool, n):
            if self._valid(combo):
                return {"slip_type": s_type, "legs": list(combo),
                        "edge_pp": round(self._edge(combo, s_type), 4),
                        "stake_total": None}
        return None
    def _valid(self, combo) -> bool:
        if len({l["player"] for l in combo}) < len(combo):
            return False
        demons = [l for l in combo if l.get("tag") == "Demon"]
        if len(demons) > self.div["demon_quota_per_slip"]:
            return False
        if self.demons_used_today + len(demons) > self.div["demon_quota_per_day"]:
            return False
        games = [l.get("game_id") for l in combo if l.get("game_id")]
        if len(games) != len(set(games)):
            return False
        return True
    def _edge(self, combo, s_type: str) -> float:
        pouts = self.pouts[s_type]
        if isinstance(pouts, (int, float)):
            return prod(l["p_hit"] for l in combo) * pouts - 1.0
        prob_all = prod(l["p_hit"] for l in combo)
        return prob_all * pouts[max(pouts, key=pouts.get)] - 1.0
