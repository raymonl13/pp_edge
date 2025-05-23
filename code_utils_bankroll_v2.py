from typing import Dict, List, Any, Tuple

def allocate_stakes(slips: List[Dict[str, Any]], bankroll: float, cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
    unit = bankroll * cfg["unit_pct"]
    demon_cap = bankroll * cfg["limits"]["demon_pct"]
    goblin_cap = bankroll * cfg["limits"]["goblin_pct"]
    spent_total = spent_demon = spent_goblin = 0.0
    out = []
    for s in slips:
        tag = "Normal"
        if any(l.get("tag") == "Demon" for l in s["legs"]):
            tag = "Demon"
        elif any(l.get("tag") == "Goblin" for l in s["legs"]):
            tag = "Goblin"
        stake = unit
        if tag == "Demon":
            if spent_demon + stake > demon_cap:
                stake = max(0.0, demon_cap - spent_demon)
            spent_demon += stake
        elif tag == "Goblin":
            if spent_goblin + stake > goblin_cap:
                stake = max(0.0, goblin_cap - spent_goblin)
            spent_goblin += stake
        if spent_total + stake > bankroll:
            stake = max(0.0, bankroll - spent_total)
        spent_total += stake
        s["stake_total"] = round(stake, 2)
        out.append(s)
        if spent_total >= bankroll:
            break
    return out, round(bankroll - spent_total, 2)
