import importlib, pandas as pd, joblib
def test_smoke(monkeypatch,tmp_path):
    mod = importlib.import_module("train_hit_prob_v2")
    def fake_load(_): 
        return pd.DataFrame({"game_date":["2025-01-01"]*4,
                             "description":["hit","out","hit","out"],
                             "batter":[1,2,3,4],
                             "pitcher":[5,6,7,8],
                             "home_team":[0,1,0,1],
                             "launch_speed":[90,85,92,81],
                             "park_factor":[100,95,102,98],
                             "barrel":[0,1,1,0]})
    monkeypatch.setattr(mod,"load_data",fake_load)
    monkeypatch.setattr(mod,"MODEL_DIR",tmp_path)
    mod.main([])
    files = list(tmp_path.glob("model_v2.pkl"))
    assert files
    obj = joblib.load(files[0])
    assert obj["auc"] > 0
