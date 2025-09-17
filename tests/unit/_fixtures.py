import pandas as pd

def make_edges_df(n=3, edge_vals=(0.05, 0.00, -0.02), payout=2.0, win_prob=0.5):
    k = min(n, len(edge_vals))
    edge_col = list(edge_vals)[:k] + [edge_vals[-1]]*(n-k)
    return pd.DataFrame({
        "edge": edge_col,
        "payout": [payout]*n,
        "win_prob": [win_prob]*n,
    })

def make_games_df():
    # Minimal schema expected by travel_miles: includes park_lat/park_lon and a date key
    return pd.DataFrame({
        "game_id":   [1, 2, 3],
        "team":      ["A","B","A"],
        "park_lat":  [37.77, 34.05, 37.77],
        "park_lon":  [-122.42, -118.24, -122.42],
        "game_date": pd.to_datetime(["2025-01-01","2025-01-02","2025-01-03"]),
    })
