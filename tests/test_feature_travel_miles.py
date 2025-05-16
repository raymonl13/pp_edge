import pandas as pd, numpy as np
from features_travel_miles import travel_miles

def _row(date, lat, lon):
    return {"game_date": pd.to_datetime(date),
            "team_id": 1, "park_lat": lat, "park_lon": lon}

def test_zero_when_first_game_or_old():
    df = pd.DataFrame([_row("2025-05-01", 37.77, -122.42)])
    assert travel_miles(df).iloc[0] == 0.0

def test_distance_within_48h():
    rows = [
        _row("2025-05-01 13:00", 37.77, -122.42),  # SF
        _row("2025-05-02 18:00", 34.05, -118.24),  # LA (~347 mi)
    ]
    df = pd.DataFrame(rows)
    miles = travel_miles(df).iloc[-1]
    assert 340 < miles < 360

