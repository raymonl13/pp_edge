import pandas as pd
def make_minimal_games_df(n=6):
    teams = [f"T{i%2+1}" for i in range(n)]
    return pd.DataFrame({
        "game_date": pd.to_datetime([f"2025-01-{i+1:02d}" for i in range(n)]),
        "team": teams,
        "events": [""] * n,
        "launch_angle": [0.0] * n,
        "batter_id": list(range(n)),
        "pitcher": list(range(n)),
        "park_lat": [0.0] * n,
        "park_lon": [0.0] * n,
        "a": list(range(n)),
        "b": [0] * n,
        "label": [0,1] * (n//2) + ([0] if n % 2 else []),
    })
def make_games_df(n=6):
    return make_minimal_games_df(n)
def make_edges_df(n=5, edge=0.05, payout=2.0, win_prob=0.55):
    return pd.DataFrame({
        "edge": [edge] * n,
        "payout": [payout] * n,
        "win_prob": [win_prob] * n,
    })
