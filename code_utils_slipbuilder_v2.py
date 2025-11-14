from itertools import combinations
from math import prod
from typing import Any, Dict, List, Tuple
from collections import Counter


class SlipBuilder:
    """
    SlipBuilder v2

    - Uses config["diversification"] and config["payouts"].
    - Enforces:
        * no duplicate players per slip
        * demon_quota_per_slip / demon_quota_per_day
        * OPTIONAL max_legs_per_game (if set in config["diversification"])
    - Builds slips greedily by slip_type in _ORDER, consuming legs as they are used.
    """

    _ORDER: Tuple[Tuple[str, int], ...] = (
        ("Power6", 6),
        ("Power4", 4),
        ("Power3", 3),
        ("Power2", 2),
        ("Flex6", 6),
        ("Flex5", 5),
        ("Flex4", 4),
    )

    def __init__(self, cfg: Dict[str, Any], *, demons_used_today: int = 0):
        self.div = cfg["diversification"]
        self.pouts = cfg["payouts"]
        self.demons_used_today = demons_used_today
        self._active = [p for p in self._ORDER if p[0] in self.pouts]

        # Optional per-game leg cap (None / missing = no limit)
        self.max_legs_per_game = self.div.get("max_legs_per_game", None)

    def build_slips(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build slips greedily:
        - Sort legs by edge_pp descending.
        - For each slip_type in priority order, repeatedly try to build a slip of that size.
        - Once a slip is built, remove its legs from the pool and continue.
        """
        slips: List[Dict[str, Any]] = []
        pool: List[Dict[str, Any]] = sorted(legs, key=lambda l: l["edge_pp"], reverse=True)

        for s_type, n in self._active:
            while True:
                slip = self._try_make(pool, s_type, n)
                if not slip:
                    break
                slips.append(slip)
                # Remove used legs from pool so they are not reused
                used_ids = {id(l) for l in slip["legs"]}
                pool = [l for l in pool if id(l) not in used_ids]

        return slips

    def _try_make(self, pool: List[Dict[str, Any]], s_type: str, n: int):
        """
        Attempt to find the first valid combo of size n from the pool for slip type s_type.
        """
        if len(pool) < n:
            return None

        for combo in combinations(pool, n):
            if self._valid(combo):
                return {
                    "slip_type": s_type,
                    "legs": list(combo),
                    "edge_pp": round(self._edge(combo, s_type), 4),
                    "stake_total": None,
                }
        return None

    def _valid(self, combo) -> bool:
        # 1) No duplicate players in a slip
        if len({l["player"] for l in combo}) < len(combo):
            return False

        # 2) Demon quotas
        demons = [l for l in combo if l.get("tag") == "Demon"]
        if len(demons) > self.div["demon_quota_per_slip"]:
            return False
        if self.demons_used_today + len(demons) > self.div["demon_quota_per_day"]:
            return False

        # 3) OPTIONAL per-game leg cap (None = no limit)
        if self.max_legs_per_game is not None:
            games = [l.get("game_id") for l in combo if l.get("game_id")]
            counts = Counter(games)
            if any(c > self.max_legs_per_game for c in counts.values()):
                return False

        return True

    def _edge(self, combo, s_type: str) -> float:
        """
        Compute slip-level edge_pp using p_hit and payout tables.

        - For Power types: payout is a scalar (multiplier).
        - For Flex types: payout is a dict; we use the max payout outcome as a simple proxy.
        """
        pouts = self.pouts[s_type]
        if isinstance(pouts, (int, float)):
            return prod(l["p_hit"] for l in combo) * pouts - 1.0

        prob_all = prod(l["p_hit"] for l in combo)
        max_outcome = max(pouts, key=pouts.get)
        return prob_all * pouts[max_outcome] - 1.0
