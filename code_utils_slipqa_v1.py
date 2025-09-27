from collections import Counter
HARD_FLAGS = {"neg_ev", "demon_quota_exceeded"}
def qa_slip(slip, cfg):
    flags = {}
    legs = slip.get("legs", [])
    flags["neg_ev"] = float(slip.get("edge_pp", 0.0)) <= 0.0
    gids = [l.get("game_id") for l in legs if "game_id" in l]
    flags["same_game_collision"] = any(c > 1 for c in Counter(gids).values())
    per_slip = int(cfg.get("diversification", {}).get("demon_quota_per_slip", 999))
    demons = sum(1 for l in legs if l.get("tag") == "Demon")
    flags["demon_quota_exceeded"] = demons > per_slip
    uniq_games = len(set(gids)) if gids else 0
    flags["low_diversity_games"] = (len(legs) >= 3) and (uniq_games / max(1, len(legs)) < 0.67)
    players = [l.get("player") for l in legs if "player" in l]
    flags["duplicate_player"] = any(c > 1 for c in Counter(players).values())
    cgroups = [l.get("correlation_group") for l in legs if "correlation_group" in l]
    flags["correlated_group"] = any(c > 1 for c in Counter(cgroups).values())
    return flags
