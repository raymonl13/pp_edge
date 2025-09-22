# Unit-lane feature stubs (must be FIRST in this file)
# - Creates a synthetic 'features' package and minimal submodules so that
#   importing code_utils_model_v1 never explodes in the unit lane.
# - Also patches bound names inside code_utils_model_v1 after import so that
#   "from features import rolling_woba" etc. refer to stubs.

import sys, types

def _zero_series(df=None, *a, **k):
    try:
        import pandas as pd
        if df is None:
            return pd.Series([], dtype=float)
        return pd.Series([0.0]*len(df), index=df.index, dtype=float)
    except Exception:
        return 0.0

# Build a minimal 'features' package with the symbols model utils import
pkg = sys.modules.get("features")
if pkg is None:
    pkg = types.ModuleType("features")
    sys.modules["features"] = pkg

def _ensure_submod(name, **attrs):
    full = f"features.{name}"
    mod = sys.modules.get(full)
    if mod is None:
        mod = types.ModuleType(full)
        sys.modules[full] = mod
        setattr(sys.modules["features"], name.split('.')[-1], mod)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod

# Common features referenced by model utils / pipeline
_ensure_submod("rolling_woba", rolling_woba=_zero_series)
_ensure_submod("wind_adj",     wind_adj=_zero_series)
_ensure_submod("platoon_split",platoon_split=_zero_series)

# Some repos do: from features import (rolling_woba, wind_adj, platoon_split, barrel_pct)
# Provide pass-throughs on the 'features' package too:
for _name in ("rolling_woba", "wind_adj", "platoon_split"):
    setattr(pkg, _name, getattr(sys.modules[f"features.{_name}"], _name))

# Any stragglers occasionally imported from 'features' (keep harmless)
if not hasattr(pkg, "barrel_pct"):
    setattr(pkg, "barrel_pct", lambda *a, **k: 0.0)

# ---- BELOW THIS LINE: your existing conftest content can remain ----

import os, pathlib, pytest, socket

def pytest_ignore_collect(path, config):
    # Keep unit lane hermetic if CI env asks for it (optional; preserve your logic)
    return False

@pytest.fixture(autouse=True)
def _no_network_in_unit_lane(monkeypatch):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        yield; return
    orig = socket.create_connection
    def _blocked(*a, **k): raise RuntimeError("network disabled in unit lane (PP_EDGE_TEST_MODE=1)")
    monkeypatch.setattr(socket, "create_connection", _blocked)
    try: yield
    finally: monkeypatch.setattr(socket, "create_connection", orig)

