import importlib, inspect, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
@pytest.mark.parametrize("n", [3, 8, 16, 32])
def test_predict_hit_prob_param(n):
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")
    predict = getattr(mu, "predict_hit_prob", None)
    if not callable(predict):
        pytest.skip("predict seam not available")
    df = pd.DataFrame({"f1": np.arange(n, dtype=float), "f2": np.zeros(n, dtype=float)})
    sig = inspect.signature(predict)
    out = predict(df, model_path="dummy.pkl") if "model_path" in sig.parameters else predict(df)
    out = np.asarray(out, dtype=float)
    assert out.shape == (n,)
    assert np.all((out >= 0.0) & (out <= 1.0))
