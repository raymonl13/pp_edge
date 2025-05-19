import datetime, os, pytest, pandas as pd

def test_edge_sheet_non_empty():
    tom = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    path = f"edge_sheet_{tom}.csv"
    if not os.path.exists(path):
        pytest.skip("edge sheet not generated")
    df = pd.read_csv(path)
    assert len(df) > 0, "edge sheet is empty"
