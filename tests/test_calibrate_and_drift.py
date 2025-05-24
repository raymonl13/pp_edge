import importlib, pandas as pd, joblib, numpy as np
def fake_model():
    from lightgbm import LGBMClassifier
    m = LGBMClassifier()
    m.fit([[0],[1]],[0,1])
    return {"model":m}
def test_calibration_monotonic(monkeypatch,tmp_path):
    cal = importlib.import_module("calibrate_hit_prob")
    monkeypatch.setattr(cal,"load_model",lambda: fake_model()["model"])
    monkeypatch.setattr(cal,"RAW",tmp_path)
    df = pd.DataFrame({"game_date":["2025-01-01"]*4,
                       "description":["hit","out","hit","out"],
                       "feat":[0,1,2,3]})
    (tmp_path/"statcast_fake.csv").write_text(df.to_csv(index=False))
    cal.main()
    assert cal.CAL_YAML.exists()
def test_drift_alert_metrics():
    drift = importlib.import_module("utils.drift_alert")
    y = [0,1,0,1]
    old = np.array([0.1,0.9,0.2,0.8])
    new = np.array([0.4,0.6,0.4,0.6])
    auc_old, auc_new, ks = drift.drift_metrics(y,old,new)
    assert ks > 0
