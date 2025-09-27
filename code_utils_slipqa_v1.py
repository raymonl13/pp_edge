from collections import Counter

def qa_slip(slip, cfg):
    flags = {}
    legs = slip.get("legs", [])
    # Negative EV
    flags["neg_ev"] = float(slip.get("edge_pp", 0.0)) <= 0.0
    # Same-game collisions (flag if any duplicate game_id)
    gids = [l.get("game_id") for l in legs if "game_id" in l]
    flags["same_game_collision"] = any(c > 1 for c in Counter(gids).values())
    # Demon quota (defensive; builder should enforce)
    per_slip = int(cfg.get("diversification", {}).get("demon_quota_per_slip", 999))
    demons = sum(1 for l in legs if l.get("tag") == "Demon")
    flags["demon_quota_exceeded"] = demons > per_slip
    return flags
