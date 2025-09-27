import os, pytest
pytestmark = pytest.mark.unit
def test_unit_lane_env_tripwire():
    assert os.getenv("PP_EDGE_TEST_MODE") == "1"
