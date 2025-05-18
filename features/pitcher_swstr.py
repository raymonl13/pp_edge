import pandas as pd

def pitcher_swstr(df: pd.DataFrame, col: str = "pitcher_swstr") -> pd.Series:
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=df.index)
