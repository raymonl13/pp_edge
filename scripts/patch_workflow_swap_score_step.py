#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text()
lines=txt.splitlines()
idxs=[i for i,l in enumerate(lines) if re.match(r'^\s*-\s*name:\s*',l)]
target=None
for i in idxs:
    if re.search(r'^\s*-\s*name:\s*Emit CSV from board\s*$', lines[i]):
        target=i; break
if target is None:
    print("step not found: Emit CSV from board"); raise SystemExit(0)
end=next((j for j in idxs if j>target), len(lines))
name_indent=re.match(r'^(\s*)', lines[target]).group(1)
lines[target]=f"{name_indent}- name: Score board"
run_set=False
for k in range(target+1,end):
    m=re.match(r'^(\s*)run:\s*(.*)$', lines[k])
    if m:
        lines[k]=f"{m.group(1)}run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml"
        run_set=True; break
if not run_set:
    ind=name_indent+"  "
    lines.insert(target+1, f"{ind}run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml")
wf.write_text("\n".join(lines))
print("OK")
