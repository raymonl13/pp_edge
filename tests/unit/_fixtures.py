import pandas as pd

def make_minimal_games_df(n=6):
    return pd.DataFrame({
        "game_date": pd.to_datetime([f"2025-01-{i+1:02d}" for i in range(n)]),
        "events": [""] * n,               # for rolling_woba
        "launch_angle": [0.0] * n,        # for wind_adj
        "batter_id": list(range(n)),      # for platoon_split
        "pitcher": list(range(n)),        # for platoon_split
        # generic columns some tests expect
        "a": list(range(n)),
        "b": [0]*n,
        "label": [0,1] * (n//2) + ([0] if n % 2 else []),
    })
