import pandas as pd

def park_factor(df: pd.DataFrame, league_avg: float = 1.0) -> pd.Series:
    for col in ("park_factor", "park_factor_x", "park_factor_y"):
        if col in df.columns and df[col].notna().any():
            return df[col].fillna(league_avg)
    return pd.Series(league_avg, index=df.index)
