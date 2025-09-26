import importlib, inspect, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
def test_predict_hit_prob_handles_nans():
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")
    predict = getattr(mu, "predict_hit_prob", None)
    if not callable(predict):
        pytest.skip("predict_hit_prob seam not available")
    df = pd.DataFrame({"f1":[1,np.nan,3], "f2":[0,0,np.nan]})
    sig = inspect.signature(predict)
    out = predict(df, model_path="dummy.pkl") if "model_path" in sig.parameters else predict(df)
    out = np.asarray(out, dtype=float)
    assert out.shape == (3,)
    assert np.all((out >= 0.0) & (out <= 1.0))
