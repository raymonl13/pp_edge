import pandas as pd

def wind_adj(df):
    """+1 tailwind >5 mph, −1 headwind <−5 mph, else 0."""
    if 'wind_speed' not in df.columns:
        return pd.Series(0, index=df.index)
    return pd.cut(df['wind_speed'], [-100, -5, 5, 100], labels=[-1, 0, 1]).astype(int)
