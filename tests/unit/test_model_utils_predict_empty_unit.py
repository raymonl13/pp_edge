import importlib, inspect, pandas as pd, numpy as np, pytest
pytestmark = pytest.mark.unit
def test_predict_hit_prob_empty_df_returns_empty_like():
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")
    predict = getattr(mu, "predict_hit_prob", None)
    if not callable(predict):
        pytest.skip("predict seam not available")
    df = pd.DataFrame({"f1": [], "f2": []})
    sig = inspect.signature(predict)
    out = predict(df, model_path="dummy.pkl") if "model_path" in sig.parameters else predict(df)
    out = np.asarray(out, dtype=float)
    assert out.size == 0
