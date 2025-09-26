import importlib, sys, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
def fake_statcast(start_dt, end_dt):
    return pd.DataFrame({"game_date":[start_dt],
                         "player_name":["Fake Guy"],
                         "some_val":[1]})
def test_ingest_tmpdir(tmp_path, monkeypatch):
    mod = importlib.import_module("code_data_ingest_statcast_v2")
    monkeypatch.setattr("code_data_ingest_statcast_v2.statcast", fake_statcast)
    monkeypatch.setattr("code_data_ingest_statcast_v2.RAW_DIR", tmp_path)
    mod.main(["--days","1"])
    csv_files = list(tmp_path.glob("statcast_*"))
    assert csv_files
    df = pd.read_csv(csv_files[0])
    assert df.iloc[0]["player_name"] == "Fake Guy"
