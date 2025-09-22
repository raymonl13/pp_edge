import os, sys, types, importlib, socket, pytest

def _zero_series(df):
    import pandas as pd
    return pd.Series(0.0, index=df.index, name="stub")

def _install_unit_feature_stubs():
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    pkg = types.ModuleType("features")
    for name in ("rolling_woba", "wind_adj", "platoon_split"):
        setattr(pkg, name, _zero_series)
    sys.modules["features"] = pkg
    try:
        mu = importlib.import_module("code_utils_model_v1")
        for name in ("rolling_woba", "wind_adj", "platoon_split"):
            setattr(mu, name, _zero_series)
    except Exception:
        pass

_install_unit_feature_stubs()

@pytest.fixture(autouse=True)
def _no_network_in_unit_lane(monkeypatch):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        yield
        return
    orig = socket.create_connection
    def _blocked(*a, **k):
        raise RuntimeError("network disabled in unit lane (PP_EDGE_TEST_MODE=1)")
    monkeypatch.setattr(socket, "create_connection", _blocked)
    try:
        yield
    finally:
        monkeypatch.setattr(socket, "create_connection", orig)
