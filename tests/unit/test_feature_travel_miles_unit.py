import importlib, importlib.util, pytest
from ._fixtures import make_games_df

pytestmark = pytest.mark.unit

def test_travel_miles_stub_returns_zeros():
    spec = importlib.util.find_spec("features_travel_miles")
    if spec is None:
        pytest.skip("features_travel_miles not found on PYTHONPATH")
    fm = importlib.import_module("features_travel_miles")

    df = make_games_df()
    out = fm.travel_miles(df)
    assert getattr(out, "shape", None) and out.shape[0] == len(df)
    assert (out.fillna(0) == 0).all()
    assert list(out.index) == list(df.index)
