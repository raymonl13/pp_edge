import pytest, math
pytestmark = pytest.mark.unit

def test_unit_lane_smoke():
    assert math.isfinite(1.0/2.0)
