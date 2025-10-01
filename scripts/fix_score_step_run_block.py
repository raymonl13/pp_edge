#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, sys

wf = Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt = wf.read_text()
lines = txt.splitlines()

# locate the Score board step
step_idxs = [i for i,l in enumerate(lines) if re.match(r'^\s*-\s*name:\s*Score board\s*$', l)]
if not step_idxs:
    print("Score board step not found", file=sys.stderr); sys.exit(1)
s = step_idxs[0]

# find end of step (next step or EOF)
next_steps = [i for i,l in enumerate(lines[s+1:], start=s+1) if re.match(r'^\s*-\s*name:\s*', l)]
e = next_steps[0] if next_steps else len(lines)

# find 'run:' within the step
run_i = None
for i in range(s+1, e):
    if re.match(r'^\s*run:\s*(\||>.*)?\s*.*$', lines[i]):
        run_i = i; break
if run_i is None:
    # inject a run line if missing
    indent = re.match(r'^(\s*)', lines[s]).group(1) + "  "
    lines.insert(s+1, f"{indent}run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml")
else:
    # replace entire run block (single or multiline) with a clean single-line run
    indent = re.match(r'^(\s*)', lines[run_i]).group(1)
    # remove existing run line and any indented block that follows
    j = run_i + 1
    while j < e and (lines[j].startswith(indent + "  ") or lines[j].strip()=="" ):
        j += 1
    del lines[run_i:j]
    lines.insert(run_i, f"{indent}run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml")

wf.write_text("\n".join(lines))
print("OK")
