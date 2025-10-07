#!/usr/bin/env python3
import sys, yaml
from pathlib import Path
WF = Path(".github/workflows/manual_edge_sheet_e2e_v3.yml")
def already_patched(steps):
    return any(s.get("name") == "Emit metrics" for s in steps)
def build_steps():
    return [
        {"name":"Emit metrics", "if":"always()", "run":"python3 scripts/emit_metrics.py"},
        {"name":"Upload metrics", "if":"always()", "uses":"actions/upload-artifact@v4", "continue-on-error": True, "with":{"name":"metrics_${{ github.run_number }}","if-no-files-found":"warn","path":"metrics_run.json"}},
        {"name":"Summarize run", "if":"always()", "run":"python3 scripts/summarize_run.py"},
        {"name":"SLO guard", "if":"always()", "run":"python3 scripts/guard_slo.py"}
    ]
def main():
    data = yaml.safe_load(WF.read_text())
    jobs = data.get("jobs") or {}
    job_key = "edge_sheet" if "edge_sheet" in jobs else next(iter(jobs))
    steps = jobs[job_key]["steps"]
    if already_patched(steps):
        print("Already patched.")
        return
    insert_at = None
    for i, s in enumerate(steps):
        if s.get("uses") == "actions/upload-artifact@v4":
            nm = (s.get("with") or {}).get("name","")
            if not str(nm).startswith("metrics_"):
                insert_at = i + 1
    if insert_at is None:
        insert_at = len(steps)
    for offset, new_step in enumerate(build_steps()):
        steps.insert(insert_at + offset, new_step)
    WF.write_text(yaml.safe_dump(data, sort_keys=False))
    print(f"Patched {WF}")
if __name__ == "__main__":
    main()
