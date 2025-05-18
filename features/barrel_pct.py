import pandas as pd

def barrel_pct(df: pd.DataFrame,
               window_pa: int = 50,
               min_pa: int = 20,
               league_avg: float = 0.06) -> pd.Series:
    bat_col = next(
        (c for c in ("batter_id", "batter", "player_id", "batter_name") if c in df.columns),
        None,
    )
    if bat_col is None:
        return pd.Series(league_avg, index=df.index)

    if "barrel" in df.columns and df["barrel"].sum() > 0:
        barrel_flag = df["barrel"]
    else:
        cond = (df["launch_speed"] >= 98) & df["launch_angle"].between(26, 30)
        barrel_flag = cond.astype(int)

    out = pd.Series(league_avg, index=df.index)
    for _, g in df.groupby(bat_col):
        pct = barrel_flag.loc[g.index].rolling(window_pa, min_periods=min_pa).mean()
        out.iloc[g.index] = pct.to_numpy()

    return out.fillna(league_avg)
