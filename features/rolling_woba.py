import pandas as pd

_EVENT_WEIGHTS = {
    "single": 0.88,
    "double": 1.247,
    "triple": 1.578,
    "home_run": 2.031,
    "walk": 0.69,
    "hit_by_pitch": 0.72,
}

def _derive_woba(df: pd.DataFrame) -> pd.Series:
    return df["events"].map(_EVENT_WEIGHTS).fillna(0.0)

def rolling_woba(df: pd.DataFrame,
                 window_days: int = 14,
                 min_pa: int = 20,
                 league_avg: float = 0.320) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float, index=df.index)

    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])

    if {"woba_value", "woba_denom"}.issubset(df.columns):
        df["_woba_pa"] = df["woba_value"] / df["woba_denom"].replace(0, pd.NA)
    else:
        df["_woba_pa"] = _derive_woba(df)

    bat_col = next(
        (c for c in ("batter_id", "batter", "player_id", "batter_name") if c in df.columns),
        None,
    )
    if bat_col is None:
        return pd.Series(league_avg, index=df.index)

    out = pd.Series(league_avg, index=df.index)
    for _, g in df.groupby(bat_col):
        g = g.sort_values("game_date")
        ser = (
            g.set_index("game_date")["_woba_pa"]
            .rolling(f"{window_days}D", closed="left", min_periods=min_pa)
            .mean()
        )
        out.iloc[g.index] = ser.to_numpy()

    return out.fillna(league_avg)
