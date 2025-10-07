#!/usr/bin/env python3
import yaml
from pathlib import Path
wf=Path(".github/workflows/manual_edge_sheet_e2e_v3.yml")
y=yaml.safe_load(wf.read_text())
jobs=y.get("jobs") or {}
key="e2e" if "e2e" in jobs else ("edge_sheet" if "edge_sheet" in jobs else next(iter(jobs)))
steps=jobs[key]["steps"]

def find(name):
    for i,s in enumerate(steps):
        if s.get("name","")==name:
            return i
    return -1

# 1) Ensure CSV guard skips on parity ERROR
g=find("Ensure CSV exists (guard)")
if g>=0:
    steps[g]["if"]="steps.parity.outputs.state != 'ERROR'"

# 2) Add model_parity.json to the QA Upload step
u=-1
for i,s in enumerate(steps):
    if s.get("uses","")== "actions/upload-artifact@v4" and (s.get("with") or {}).get("name","").startswith("qa_alloc_"):
        u=i; break
if u>=0:
    w=steps[u].setdefault("with",{})
    paths=w.get("path")
    block = ""
    if isinstance(paths,str):
        block=paths
    elif isinstance(paths,list):
        block="\n".join(paths)
    if "model_parity.json" not in block:
        block = (block.rstrip()+"\n" if block else "") + "model_parity.json"
        w["path"]=block

wf.write_text(yaml.safe_dump(y, sort_keys=False))
print("patched")
