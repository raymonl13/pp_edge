import pandas as pd, pytest, importlib

pytestmark = pytest.mark.unit

def test_travel_miles_stub_returns_zeros():
    spec = importlib.util.find_spec("features_travel_miles")
    if spec is None:
        pytest.skip("features_travel_miles not found on PYTHONPATH")
    fm = importlib.import_module("features_travel_miles")

    # Align to feature contract: include game_date (keep date as alias for later refactor)
    df = pd.DataFrame({
        "game_id":[1,2,3],
        "team":["A","B","A"],
        "lat":[37.77, 34.05, 37.77],
        "lon":[-122.42, -118.24, -122.42],
        "game_date": pd.to_datetime(["2025-01-01","2025-01-02","2025-01-03"])
    })
    df["date"] = df["game_date"]  # harmless alias

    out = fm.travel_miles(df)
    assert getattr(out, "shape", None) and out.shape[0] == len(df)
    assert (out.fillna(0) == 0).all()
    assert list(out.index) == list(df.index)
