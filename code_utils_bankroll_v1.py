def size_bet(edge_pp, bankroll_cfg, bankroll_state, tag=None):
    start = bankroll_cfg['starting']
    kf = bankroll_cfg.get('kelly_fraction', 1.0)
    over = bankroll_cfg.get('sizing', {}).get('kelly_fraction_override', {})
    if tag in over:
        kf = over[tag]
    raw = edge_pp * kf * start
    max_roll = bankroll_cfg.get('max_bet_fraction_of_roll', 1.0) * start
    size = min(raw, max_roll)
    daily_cap = bankroll_cfg.get('daily_max_staked_pct', 1.0) * start
    used = bankroll_state.get('staked_today', 0.0)
    if used >= daily_cap:
        return 0.0
    size = min(size, daily_cap - used)
    bankroll_state['staked_today'] = used + size
    return round(size, 2)
