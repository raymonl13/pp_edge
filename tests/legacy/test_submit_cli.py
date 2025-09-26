import json, pathlib, subprocess, sys, os, tempfile

def _payload(tmp):
    p = tmp / "slips.json"
    p.write_text(json.dumps([{"player": "A", "line": 1.5, "pick": "over"}]))
    return p

def test_dry_run(tmp_path):
    payload = _payload(tmp_path)
    r = subprocess.run(
        [sys.executable, "code_cli_submit_slips_v1.py", str(payload), "--dry-run"],
        capture_output=True, text=True, cwd=pathlib.Path(__file__).parents[1],
    )
    assert json.loads(r.stdout)["count"] == 1

def test_live(tmp_path):
    payload = _payload(tmp_path)
    env = dict(os.environ)
    env["PP_EDGE_TEST_MODE"] = "1"
    subprocess.check_call(
        [sys.executable, "code_cli_submit_slips_v1.py", str(payload), "--live"],
        cwd=pathlib.Path(__file__).parents[1],
        env=env,
    )
