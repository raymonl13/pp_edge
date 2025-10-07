#!/usr/bin/env python3
import os, sys, json, glob
from pathlib import Path
import yaml
def glob_exists(pattern: str) -> bool:
    if Path(pattern).exists():
        return True
    return bool(glob.glob(f"**/{pattern}", recursive=True))
def load_metrics() -> dict:
    try:
        return json.loads(Path("metrics_run.json").read_text())
    except Exception:
        return {}
def load_slo() -> dict:
    try:
        return yaml.safe_load(Path("ci/slo.yaml").read_text())
    except Exception:
        return {"router":{"min_row_count":100,"max_retry_count":5},"qa":{"must_have":["edge_sheet_${{ env.DAY }}.csv","run_meta.txt"]}}
def main():
    m = load_metrics() or {}
    s = load_slo() or {}
    reasons = []
    r = m.get("router") or {}
    min_rows = ((s.get("router") or {}).get("min_row_count"))
    max_retry = ((s.get("router") or {}).get("max_retry_count"))
    row_count = r.get("row_count")
    retry_count = r.get("retry_count")
    if (row_count is not None) and (min_rows is not None) and (row_count < min_rows):
        reasons.append(f"router.row_count<{min_rows}")
    if (retry_count is not None) and (max_retry is not None) and (retry_count > max_retry):
        reasons.append(f"router.retry_count>{max_retry}")
    day = os.environ.get("DAY", "")
    for req in (s.get("qa") or {}).get("must_have", []):
        req = req.replace("${{ env.DAY }}", day)
        if not glob_exists(req):
            reasons.append(f"missing:{req}")
    result = {"slo": ("FAIL" if reasons else "PASS"), "reasons": reasons}
    print(json.dumps(result))
    sys.exit(1 if reasons else 0)
if __name__ == "__main__":
    main()
