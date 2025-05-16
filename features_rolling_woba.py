import pandas as pd

def rolling_woba(df, window_days=14, min_pa=20, league_avg=0.320):
    if df.empty:
        return pd.Series(dtype=float, index=df.index)
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["_woba_pa"] = df["woba_value"] / df["woba_denom"].replace(0, pd.NA)
    out = pd.Series(index=df.index, dtype=float)
    for _, g in df.groupby("batter_id"):
        r = (
            g.set_index("game_date")["_woba_pa"]
            .rolling(f"{window_days}D", closed="left", min_periods=min_pa)
            .mean()
        )
        out.loc[g.index] = r.values
    return out.fillna(league_avg)
