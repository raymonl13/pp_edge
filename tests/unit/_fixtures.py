import pandas as pd
from datetime import datetime

def make_minimal_games_df(n=5):
    # Satisfy all known feature contracts used in build_feature_df
    return pd.DataFrame({
        "game_date": pd.to_datetime([f"2025-01-{i+1:02d}" for i in range(n)]),
        "events": [""]*n,
        "launch_angle": [0.0]*n,
        "batter_id": list(range(n)),
        "pitcher": list(range(n)),
        # generic columns used by adhoc tests
        "a": list(range(n)),
        "b": [0]*n,
        "label": [0,1] * (n//2) + [0]*(n%2),
    })
