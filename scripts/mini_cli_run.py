import json, tempfile, subprocess, sys, pathlib
sample = [
    {"slip_type": "Power2", "stake_total": 20, "edge_pp": 0.15},
    {"slip_type": "Power3", "stake_total": 20, "edge_pp": 0.12},
]
with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as fh:
    json.dump(sample, fh)
    fh.flush()
    subprocess.run([sys.executable, "cli/code_cli_submit_slips_v1.py", fh.name, "--dry-run"])
