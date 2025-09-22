import pandas as pd

def make_minimal_games_df(n=6):
    return pd.DataFrame({
        "game_date": pd.to_datetime([f"2025-01-{i+1:02d}" for i in range(n)]),
        "events": [""] * n,               # for rolling_woba (stubbed to 0 in unit lane)
        "launch_angle": [0.0] * n,        # for wind_adj (stubbed to 0)
        "batter_id": list(range(n)),      # for platoon_split (stubbed to 0)
        "pitcher": list(range(n)),        # for platoon_split (stubbed to 0)
        "a": list(range(n)),
        "b": [0]*n,
        "label": [0,1] * (n//2) + ([0] if n % 2 else []),
    })
