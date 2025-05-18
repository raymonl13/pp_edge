import pandas as pd, numpy as np

EARTH_R = 3959.0

def _haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * EARTH_R * np.arcsin(np.sqrt(a))

def travel_miles(df: pd.DataFrame, window_avg: float = 500.0) -> pd.Series:
    if {"team_id", "game_date"}.issubset(df.columns):
        out = pd.Series(window_avg, index=df.index)
        for _, g in df.groupby("team_id"):
            g = g.sort_values("game_date")
            if {"park_lat", "park_lon"}.issubset(g.columns):
                dist = _haversine(
                    g["park_lat"], g["park_lon"],
                    g["park_lat"].shift(), g["park_lon"].shift()
                )
            else:
                dist = pd.Series(window_avg, index=g.index)
            dist.iloc[0] = 0.0
            dist = dist.fillna(window_avg)
            out.iloc[g.index] = dist.to_numpy()
        return out
    return pd.Series(window_avg, index=df.index)
