#!/usr/bin/env python3
import yaml
from pathlib import Path
wf=Path(".github/workflows/manual_edge_sheet_e2e_v3.yml")
y=yaml.safe_load(wf.read_text())
jobs=y.get("jobs") or {}
key="e2e" if "e2e" in jobs else ("edge_sheet" if "edge_sheet" in jobs else next(iter(jobs)))
steps=jobs[key]["steps"]
names=[s.get("name","") for s in steps]
def step(n): 
    return next((i for i,s in enumerate(steps) if s.get("name","")==n),-1)
if "Build submit payload (dry-run)" not in names:
    idx=step("Summarize run")
    ins_idx=idx if idx>=0 else len(steps)
    steps.insert(ins_idx,{"name":"Build submit payload (dry-run)","if":"always()","run":"python3 scripts/build_submit_payload.py"})
if "Upload submit payload" not in names:
    u_idx=step("Build submit payload (dry-run)")
    steps.insert((u_idx+1 if u_idx>=0 else len(steps)),{
        "name":"Upload submit payload",
        "if":"always()",
        "uses":"actions/upload-artifact@v4",
        "continue-on-error": True,
        "with":{"name":"submit_payload_${{ github.run_number }}","if-no-files-found":"warn","path":"submit_payload.json"}
    })
wf.write_text(yaml.safe_dump(y, sort_keys=False))
print("patched")
