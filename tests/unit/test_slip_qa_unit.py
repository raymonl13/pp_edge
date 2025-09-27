import json, sys, subprocess, pytest, os
pytestmark = pytest.mark.unit

CSV = """player,game_id,p_hit,edge_pp,tag
A,g1,0.61,0.12,
B,g2,0.58,0.09,
C,g3,0.63,0.13,
D,g4,0.57,0.08,
E,g5,0.60,0.11,Demon
F,g6,0.55,0.07,
"""

def test_offline_outputs_review_and_filters_neg_ev(tmp_path):
    slate = tmp_path / "slate.csv"
    slate.write_text(CSV)
    out = tmp_path / "slips.json"
    r = subprocess.run([sys.executable, "cli/run_offline.py", str(slate), str(out), "--unit", "1"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    review = tmp_path / "slips_review.json"
    assert out.exists() and review.exists()

    data = json.loads(out.read_text())
    review_data = json.loads(review.read_text())
    assert "slips" in data and "slips" in review_data

    # Approved-only in out; all slips (with flags) in review
    approved = data["slips"]
    all_slips = review_data["slips"]
    assert len(all_slips) >= len(approved)

    # At least one slip should be flagged negative EV and thus filtered out
    flagged = [s for s in all_slips if s.get("_qa_flags", {}).get("neg_ev")]
    assert len(flagged) >= 1
    assert all(s not in approved for s in flagged)
