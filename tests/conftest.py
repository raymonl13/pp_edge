import sys, types
if 'xgboost' not in sys.modules:
    sys.modules['xgboost'] = types.ModuleType('xgboost')
import os, sys, types, socket, pathlib, pytest, pandas as pd
def _zero_series(df=None, *_, **__):
    if df is None: return pd.Series([], dtype=float)
    return pd.Series([0.0]*len(df), index=df.index, name="stub")
def _install_unit_feature_stubs():
    if os.getenv("PP_EDGE_TEST_MODE") != "1": return
    pkg = types.ModuleType("features")
    def __getattr__(_): return _zero_series
    pkg.__getattr__ = __getattr__
    for n in ("rolling_woba","wind_adj","platoon_split","barrel_pct","pitcher_swstr"):
        setattr(pkg, n, _zero_series)
    sys.modules["features"] = pkg
    try:
        mu = __import__("code_utils_model_v1")
        for n in ("rolling_woba","wind_adj","platoon_split","barrel_pct","pitcher_swstr"):
            setattr(mu, n, _zero_series)
    except Exception:
        pass
_install_unit_feature_stubs()
@pytest.fixture(autouse=True)
def _no_network_in_unit_lane(monkeypatch):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        yield; return
    orig = socket.create_connection
    def _blocked(*a, **k): raise RuntimeError("network disabled in unit lane (PP_EDGE_TEST_MODE=1)")
    monkeypatch.setattr(socket, "create_connection", _blocked)
    try: yield
    finally: monkeypatch.setattr(socket, "create_connection", orig)
def pytest_ignore_collect(collection_path: pathlib.Path, path=None):
    return "tests/legacy/" in str(collection_path)
