import pandas as pd

def rolling_barrel(df: pd.DataFrame, window_pa: int = 100):
    """Rolling barrel rate over last 100 PA."""
    df = df.copy()
    df['is_barrel'] = df['barrel'].fillna(0)
    gb = df.groupby('batter')
    cum_pa = gb.cumcount() + 1
    cum_barrel = gb['is_barrel'].cumsum()
    pct = (cum_barrel - cum_barrel.shift(window_pa).fillna(0)) / window_pa
    return pct
