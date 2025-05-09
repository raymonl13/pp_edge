from typing import List, Dict

_ICON_VARIANT_MAP: Dict[int, str] = {1: "More", 2: "Less", 3: "Fantasy", 4: "Combo", 5: "Standard"}

def _simplify_props(feeds: Dict) -> List[Dict]:
    rows = feeds["projections"]["data"]
    simplified: List[Dict] = []
    for item in rows:
        attr = item.get("attributes", item)
        variant = _ICON_VARIANT_MAP.get(attr.get("icon_id"), str(attr.get("icon_id")))
        simplified.append(
            {
                "player":  attr.get("description"),
                "team":    attr.get("team_abbr"),
                "stat":    attr.get("stat_type"),
                "line":    attr.get("line_score"),
                "variant": variant,
                "edge_pp": 0.0,
            }
        )
    return simplified
