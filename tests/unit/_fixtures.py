import pandas as pd

def make_edges_df(n=3, edge_vals=(0.05, 0.00, -0.02), payout=2.0, win_prob=0.5):
    k = min(n, len(edge_vals))
    edge_col = list(edge_vals)[:k] + [edge_vals[-1]]*(n-k)
    return pd.DataFrame({
        "edge": edge_col,
        "payout": [payout]*n,
        "win_prob": [win_prob]*n,
    })
