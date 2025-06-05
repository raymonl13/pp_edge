"""
Verify that the calibration YAML is present and matches its recorded checksum.
Run `scripts/gen_cal_checksum.sh` locally to regenerate when the file changes.
"""
from pathlib import Path
import hashlib, pytest

CAL_FILE   = Path("model_assets/calibration_params_v2.yaml")
CHECK_FILE = Path("model_assets/calibration_params_v2.sha256")

@pytest.mark.skipif(not CAL_FILE.exists(), reason="asset missing in fork")
def test_checksum_ok():
    recorded = CHECK_FILE.read_text().split()[0]
    actual   = hashlib.sha256(CAL_FILE.read_bytes()).hexdigest()
    assert actual == recorded, "calibration_params_v2.yaml checksum mismatch"
