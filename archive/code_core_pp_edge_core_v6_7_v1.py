
""" PP Edge Core Engine v6.7 (stub) """

from typing import Dict, Any, List

def _simplify_props(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "player": p.get("player"),
            "stat_type": p.get("stat_type"),
            "line": p.get("line"),
            "over_odds": p.get("over_odds"),
            "under_odds": p.get("under_odds"),
            "tag": p.get("tag", "Default"),
        }
        for p in raw
    ]

def run_engine(props: List[Dict[str, Any]]) -> None:
    props = _simplify_props(props)
    for p in props:
        print(f"[DEMO] {p['player']} {p['stat_type']} @ {p['line']}  ->  edge TBD")

if __name__ == "__main__":
    import json, pathlib
    sample = json.loads((pathlib.Path(__file__).with_name("data_feed_sample.json")).read_text())
    run_engine(sample["projections"])
