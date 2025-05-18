import pandas as pd, pathlib, functools
import numpy as np

@functools.lru_cache
def get_park_factors() -> pd.DataFrame:
    pf = pd.read_csv(pathlib.Path("park_factors.csv"))
    pf = pf.rename(columns={
        "home_team": "team_id",
        "team": "team_id",
        "pf": "park_factor",
        "lat": "park_lat",
        "lon": "park_lon",
    })
    for col in ["park_lat", "park_lon"]:
        if col not in pf.columns:
            pf[col] = np.nan
    return pf[["team_id", "park_factor", "park_lat", "park_lon"]]
