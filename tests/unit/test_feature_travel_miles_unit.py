import pandas as pd, pytest, importlib
pytestmark = pytest.mark.unit
def test_travel_miles_stub_returns_zeros():
    try:
        mod = importlib.import_module("features_travel_miles")
    except Exception as e:
        pytest.skip(f"features_travel_miles not importable: {e}")
    if not hasattr(mod,"travel_miles"):
        pytest.skip("travel_miles seam not available")
    n = 6
    df = pd.DataFrame({
        "game_date": pd.to_datetime([f"2025-01-{i+1:02d}" for i in range(n)]),
        "team": ["T1","T2","T1","T2","T1","T2"],
        "park_lat": [0.0]*n,
        "park_lon": [0.0]*n,
    })
    out = mod.travel_miles(df)
    assert len(out) == n
    assert (getattr(out,"to_numpy",lambda: out)() == 0).all()
