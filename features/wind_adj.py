import pandas as pd, numpy as np

def wind_adj(df: pd.DataFrame) -> pd.Series:
    cols = {"wind_speed", "wind_dir"}
    if cols.issubset(df.columns):
        spd = df["wind_speed"].fillna(df["wind_speed"].median())
        ang = np.deg2rad(df["wind_dir"].fillna(0))
        return (spd * np.cos(ang)).astype(float)
    centered = df["launch_angle"] - df["launch_angle"].mean()
    return (centered / centered.abs().max()).astype(float)
