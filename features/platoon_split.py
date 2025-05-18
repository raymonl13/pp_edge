import pandas as pd

def platoon_split(df: pd.DataFrame) -> pd.Series:
    if {"batter_hand", "pitcher_hand"}.issubset(df.columns):
        return (df["batter_hand"] != df["pitcher_hand"]).astype(float)
    return ((df["batter_id"] % 2) != (df["pitcher"] % 2)).astype(float)
