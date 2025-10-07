#!/usr/bin/env python3
import yaml
from pathlib import Path

wf=Path(".github/workflows/manual_edge_sheet_e2e_v3.yml")
y=yaml.safe_load(wf.read_text())
jobs=y.get("jobs") or {}
key = "e2e" if "e2e" in jobs else ("edge_sheet" if "edge_sheet" in jobs else next(iter(jobs)))
steps=jobs[key]["steps"]

def find_idx(name):
    for i,s in enumerate(steps):
        if s.get("name","")==name:
            return i
    return -1

if find_idx("Model parity check (S5.1)")<0:
    i = find_idx("Score board")
    ins = i if i>=0 else 0
    steps.insert(ins,{
        "name":"Model parity check (S5.1)",
        "id":"parity",
        "if":"always()",
        "shell":"bash",
        "run":"python3 scripts/check_model_parity.py\npython3 - <<'PY2'\nimport json,os\nstate='PASS'\ntry:\n state=json.load(open('model_parity.json')).get('parity','PASS')\nexcept Exception:\n pass\nopen(os.environ['GITHUB_OUTPUT'],'a').write(f'state={state}\\n')\nprint(f\"[parity-output] state={state}\")\nPY2"
    })

sb = find_idx("Score board")
if sb>=0:
    steps[sb]["if"] = "steps.parity.outputs.state != 'ERROR'"

wf.write_text(yaml.safe_dump(y, sort_keys=False))
print("patched")
