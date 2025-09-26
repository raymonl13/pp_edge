from pathlib import Path
from code_train_hit_prob_v1 import train

def test_train_smoke(tmp_path):
    train(tmp_path / "dummy.pkl", rows=500)
