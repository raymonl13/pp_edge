import pandas as pd

def platoon_split(df):
    """1 if batter & pitcher are opposite-handed, else 0."""
    if {'stand', 'p_throws'}.issubset(df.columns):
        return (df['stand'] != df['p_throws']).astype(int)
    return pd.Series(0, index=df.index)
