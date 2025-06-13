import os, subprocess, tempfile, pytest
@pytest.mark.skipif(not os.path.exists("data/raw/statcast_90d.csv"),reason="fixture dataset missing")
def test_train_hit_prob_v3():
    with tempfile.TemporaryDirectory() as tmp:
        mdl=os.path.join(tmp,"m.pkl")
        sha=os.path.join(tmp,"m.sha")
        proc=subprocess.run(["python","scripts/train_hit_prob_v3.py","--input","data/raw/statcast_90d.csv","--model-out",mdl,"--sha-out",sha],capture_output=True,text=True,check=True)
        assert os.path.exists(mdl)
        assert os.path.exists(sha)
        digest=open(sha).read().strip()
        assert len(digest)==64
        auc=float(next(x.split("=")[1] for x in proc.stdout.split() if x.startswith("AUC")))
        assert auc>=0.60
