import json, subprocess, tempfile, pathlib, sys

SAMPLE = [
    {"slip_type": "Power2", "stake_total": 20, "edge_pp": 0.15},
    {"slip_type": "Power3", "stake_total": 20, "edge_pp": 0.12},
]

def test_dry_run_exits_zero(tmp_path: pathlib.Path):
    payload = tmp_path / "slips.json"
    payload.write_text(json.dumps(SAMPLE))
    proc = subprocess.run(
        [sys.executable, "cli/code_cli_submit_slips_v1.py", str(payload), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["count"] == 2
