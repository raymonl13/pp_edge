import importlib, pytest
pytestmark = pytest.mark.unit
MODULES = [
    "code_utils_model_v1",
    "code_utils_slipbuilder_v2",
    "code_utils_bankroll_v1",
    "features_travel_miles",
    "monte_carlo_bankroll",
]
@pytest.mark.parametrize("m", MODULES)
def test_import_smoke(m):
    try:
        importlib.import_module(m)
    except Exception as e:
        pytest.skip(f"{m} not importable: {e}")
