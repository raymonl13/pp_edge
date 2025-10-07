#!/usr/bin/env python3
import os, sys, json, glob
from pathlib import Path
try:
    import yaml
except Exception:
    print(json.dumps({"slo":"FAIL","reasons":["PyYAML_missing"]}))
    sys.exit(1)

def glob_exists(p):
    if Path(p).exists():
        return True
    return bool(glob.glob(f"**/{p}", recursive=True))

def load_metrics():
    try:
        return json.loads(Path("metrics_run.json").read_text())
    except Exception:
        return {}

def load_slo():
    try:
        return yaml.safe_load(Path("ci/slo.yaml").read_text())
    except Exception:
        return {"router":{"min_row_count":100,"max_retry_count":5},"qa":{"must_have":["edge_sheet_${{ env.DAY }}.csv","run_meta.txt"]}}

def read_model_state():
    try:
        for ln in Path("run_meta.txt").read_text().splitlines():
            if ln.startswith("MODEL_STATE="):
                return ln.split("=",1)[1].strip()
    except Exception:
        pass
    return "OK"

def main():
    m = load_metrics() or {}
    s = load_slo() or {}
    reasons = []

    # router checks
    r = m.get("router") or {}
    min_rows = ((s.get("router") or {}).get("min_row_count"))
    max_retry = ((s.get("router") or {}).get("max_retry_count"))
    row_count = r.get("row_count")
    retry_count = r.get("retry_count")

    if (row_count is not None) and (min_rows is not None) and (row_count < min_rows):
        reasons.append(f"router.row_count<{min_rows}")
    if (retry_count is not None) and (max_retry is not None) and (retry_count > max_retry):
        reasons.append(f"router.retry_count>{max_retry}")

    # must-have QA files
    day = os.environ.get("DAY","")
    model_state = read_model_state()
    for req in (s.get("qa") or {}).get("must_have", []):
        req_resolved = req.replace("${{ env.DAY }}", day)
        if ("edge_sheet_" in req_resolved) and (model_state == "ERROR"):
            continue
        if not glob_exists(req_resolved):
            reasons.append(f"missing:{req_resolved}")

    out = {"slo": ("FAIL" if reasons else "PASS"), "reasons": reasons}
    print(json.dumps(out))
    sys.exit(1 if reasons else 0)

if __name__ == "__main__":
    main()
