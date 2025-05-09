import pandas as pd
from pathlib import Path
from features import (
    rolling_woba, rolling_barrel, pitcher_swstr,
    park_factor, wind_adj, travel_miles, platoon_split
)

def test_feature_outputs():
    df = pd.read_csv(Path('data/raw/statcast_with_parks.csv')).head(500)
    funcs = [
        rolling_woba.rolling_woba,
        rolling_barrel.rolling_barrel,
        pitcher_swstr.pitcher_swstr,
        park_factor.park_factor,
        wind_adj.wind_adj,
        travel_miles.travel_miles,
        platoon_split.platoon_split,
    ]
    for f in funcs:
        out = f(df)
        assert len(out) == len(df)
