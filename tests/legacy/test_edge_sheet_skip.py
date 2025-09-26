# tests/test_edge_sheet_skip.py
import subprocess, sys, shutil
from pathlib import Path

def test_edge_sheet_skips_cleanly_when_model_absent(tmp_path, monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo)
    assets = repo / "model_assets"
    if assets.exists():
        shutil.rmtree(assets)
    p = subprocess.run(
        [sys.executable, "run_edge_sheet.py", "--date", "2099-01-01"],
        capture_output=True, text=True
    )
    msg = (p.stdout + p.stderr).lower()
    assert p.returncode == 0
    assert "missing model" in msg or "skipping" in msg

