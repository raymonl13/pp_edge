import pandas as pd
import numpy as np

_EARTH_RADIUS_MI = 3958.8  # mean Earth radius in miles


def _haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_MI * np.arcsin(np.sqrt(a))


def travel_miles(df: pd.DataFrame, window_h=48) -> pd.Series:
    """
    Distance (miles) a team has traveled since its previous game *within* the
    last `window_h` hours.  Requires columns:
        • team_id              (int/str) – batting team
        • game_date            (datetime64[ns])
        • park_lat, park_lon   (floats, ballpark coordinates)
    """
    if df.empty:
        return pd.Series(dtype=float, index=df.index)

    out = pd.Series(0.0, index=df.index)
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])

    for _, g in df.groupby("team_id"):
        g_sorted = g.sort_values("game_date")
        dist = _haversine(
            g_sorted["park_lat"].shift(),
            g_sorted["park_lon"].shift(),
            g_sorted["park_lat"],
            g_sorted["park_lon"],
        )
        dt_hr = (g_sorted["game_date"] - g_sorted["game_date"].shift()).dt.total_seconds() / 3600
        dist = dist.where(dt_hr <= window_h, 0.0)
        out.loc[g_sorted.index] = dist.fillna(0.0)

    return out
