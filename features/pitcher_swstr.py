import pandas as pd

def pitcher_swstr(df: pd.DataFrame, window_ip: int = 30):
    """Rolling swinging-strike% (approx) over last 30 IP."""
    df = df.copy()
    df['is_swstr'] = df['description'].str.contains('swinging_strike', na=False).astype(int)
    gb = df.groupby('pitcher')
    cum_sw = gb['is_swstr'].cumsum()
    cum_tot = gb.cumcount() + 1
    pct = (cum_sw - cum_sw.shift(window_ip*15).fillna(0)) / (
        (cum_tot - cum_tot.shift(window_ip*15).fillna(0)).replace(0, pd.NA)
    )
    return pct
