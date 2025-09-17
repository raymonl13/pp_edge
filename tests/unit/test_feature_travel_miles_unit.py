import pandas as pd, pytest
pytestmark = pytest.mark.unit

def test_travel_miles_stub_returns_zeros():
    try:
        import features_travel_miles as fm
    except Exception as e:
        pytest.skip(f"features_travel_miles not importable in unit lane: {e}")
    df = pd.DataFrame({
        "game_id":[1,2,3],
        "team":["A","B","A"],
        "lat":[37.77, 34.05, 37.77],
        "lon":[-122.42, -118.24, -122.42],
        "date": pd.to_datetime(["2025-01-01","2025-01-02","2025-01-03"])
    })
    out = fm.travel_miles(df)
    assert hasattr(out, "shape") and out.shape[0] == len(df)
    assert (out.fillna(0) == 0).all()
    assert getattr(out, "name", "miles") in ("miles","travel_miles","distance")
    assert list(out.index) == list(df.index)
