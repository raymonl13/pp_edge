from typing import Iterable, Dict, Any
from itertools import combinations
from code_utils_slipbuilder_v1 import SlipBuilder
from code_utils_model_v1 import predict_hit_prob


def _safe_cfg(cfg: dict, key: str, *, default):
    return cfg.get(key,
                   cfg.get("pricing", {}).get(key,
                   cfg.get("filters", {}).get(key, default)))


def run_pipeline(raw_legs: Iterable[Dict[str, Any]],
                 cfg: Dict[str, Any]) -> list[dict]:
    payout   = _safe_cfg(cfg, "payout_per_leg", default=10.0)
    min_edge = _safe_cfg(cfg, "min_edge_pp",     default=0.03)

    all_priced = list(_price(raw_legs, payout))
    priced     = [l for l in all_priced if l["edge_pp"] >= min_edge]
    print(f"→ {len(priced)} legs with edge ≥ {min_edge:.02f}")
    slips      = SlipBuilder(cfg).build_slips(priced)
    return slips


def _price(legs: Iterable[Dict[str, Any]], payout: float):
    tier = "demon" if payout >= 25 else "goblin"
    for leg in legs:
        prob = float(predict_hit_prob(leg))
        edge = round((prob * payout) - 1, 4)
        yield {**leg,
               "prob":    prob,
               "p_hit":   prob,
               "edge_pp": edge,
               "tier":    tier}
