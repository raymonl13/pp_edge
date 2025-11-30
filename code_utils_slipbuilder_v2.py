#!/usr/bin/env python3
from __future__ import annotations
"""
SlipBuilder v2 — NBA v0.1 hotfix profile

- Allows same-game legs (no game_id ban).
- Hard guard: NO duplicate player in a slip.
- Optional soft limits read from cfg dict (if present), but default permissive.
- Builds Power6 first, then Power4 (greedy, top-down by edge).
"""

from typing import Any, Dict, List, Iterable
from itertools import combinations

def _player_key(leg: Dict[str, Any]) -> str:
    # accept either "player_name" or "player"
    return (leg.get("player_name") or leg.get("player") or "").strip().lower()

def _team(leg: Dict[str, Any]) -> str:
    return (leg.get("team") or "").strip().upper()

def _odds_type(leg: Dict[str, Any]) -> str:
    return (leg.get("odds_type") or "").strip().lower()

class SlipBuilder:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = cfg or {}
        nba_cfg = (cfg.get("nba") or {})
        div = (nba_cfg.get("diversification") or {})
        # Permissive defaults for v0.1
        self.max_same_team_per_slip = int(div.get("max_same_team_per_slip", 6))
        self.max_demon_per_slip     = int(div.get("max_demon_per_slip", 6))
        self.max_goblin_per_slip    = int(div.get("max_goblin_per_slip", 6))
        self.allow_same_game        = bool(div.get("allow_same_game", True))
        self.max_slips              = int(nba_cfg.get("max_slips", 3))
        self.target_leg_counts      = nba_cfg.get("target_leg_counts", [6, 4])

    def _valid(self, combo: List[Dict[str, Any]]) -> bool:
        seen_players = set()
        team_counts: Dict[str, int] = {}
        tier_counts = {"demon": 0, "goblin": 0}

        for leg in combo:
            pk = _player_key(leg)
            if not pk:
                return False
            if pk in seen_players:
                return False
            seen_players.add(pk)

            t = _team(leg)
            if t:
                team_counts[t] = team_counts.get(t, 0) + 1
                if team_counts[t] > self.max_same_team_per_slip:
                    return False

            tier = _odds_type(leg)
            if tier in tier_counts:
                tier_counts[tier] += 1
                if tier == "demon" and tier_counts[tier] > self.max_demon_per_slip:
                    return False
                if tier == "goblin" and tier_counts[tier] > self.max_goblin_per_slip:
                    return False

        # game correlation: v0.1 allows same-game; if you ever want to ban, enforce here.
        return True

    def build(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sort candidates by descending edge (fall back to p_hit if present)
        def edge(leg: Dict[str, Any]) -> float:
            try:
                return float(leg.get("edge_pp", leg.get("p_hit", 0.5) - 0.5))
            except Exception:
                return 0.0

        ranked = sorted(legs, key=edge, reverse=True)
        slips: List[Dict[str, Any]] = []

        for L in self.target_leg_counts:
            # Greedy pre-screen: keep top ~80 legs to bound search
            pool = ranked[:80] if len(ranked) > 80 else ranked
            # Quick greedy attempt: walk down and pick first L unique players
            greedy: List[Dict[str, Any]] = []
            seen = set()
            for leg in pool:
                pk = _player_key(leg)
                if not pk or pk in seen:
                    continue
                greedy.append(leg)
                seen.add(pk)
                if len(greedy) == L:
                    break
            if len(greedy) == L and self._valid(greedy):
                slips.append(_slip_from_legs(greedy, L))
                if len(slips) >= self.max_slips:
                    break
                # continue searching other L sizes as configured

            # If greedy didn’t hit, try limited combinations across top subset
            top_for_combo = pool[:30]  # bound combinatorics
            for combo in combinations(top_for_combo, L):
                combo = list(combo)
                if self._valid(combo):
                    slips.append(_slip_from_legs(combo, L))
                    if len(slips) >= self.max_slips:
                        break
            if len(slips) >= self.max_slips:
                break

        return slips

def _slip_from_legs(legs: List[Dict[str, Any]], L: int) -> Dict[str, Any]:
    # simple aggregate edge: sum of leg edges
    E = 0.0
    for leg in legs:
        try:
            E += float(leg.get("edge_pp", float(leg.get("p_hit", 0.5)) - 0.5))
        except Exception:
            pass
    summary = "; ".join([
        f"{leg.get('player_name') or leg.get('player','?')} "
        f"({leg.get('team','')}) {leg.get('market','')} {leg.get('line','')}"
        for leg in legs
    ])
    return {
        "slip_type": f"Power{L}",
        "edge_pp": round(E, 6),
        "stake_total": "",
        "num_legs": L,
        "legs": legs,
        "legs_summary": summary,
    }

# ---- Backward-compat shim so wrappers can always call `build_slips` ----
try:
    # If SlipBuilder doesn't expose build_slips, alias to any known builder.
    if not hasattr(SlipBuilder, "build_slips"):
        def _build_slips_shim(self, legs):
            for name in ("build_slips", "build", "generate_slips", "generate", "__call__"):
                fn = getattr(self, name, None)
                if callable(fn):
                    return fn(legs)
            raise AttributeError("SlipBuilder lacks a build/generate method.")
        SlipBuilder.build_slips = _build_slips_shim  # type: ignore[attr-defined]
except Exception:
    # Don't make import fail if something odd happens
    pass
