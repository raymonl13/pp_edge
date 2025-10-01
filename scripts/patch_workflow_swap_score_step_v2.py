#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text()
lines=txt.splitlines()

def find_steps_indices(ls):
    return [i for i,l in enumerate(ls) if re.match(r'^\s*-\s*name:\s*',l)]

def step_bounds(ls, idxs, k):
    start = idxs[k]
    end = idxs[k+1] if k+1 < len(idxs) else len(ls)
    return start, end

def ensure_scorer_step(ls):
    if any("scripts/score_board.py" in l for l in ls):
        return ls, "ALREADY_WIRED"
    steps_hdr = None
    for i,l in enumerate(ls):
        if re.match(r'^\s*steps:\s*$', l):
            steps_hdr = i
            break
    if steps_hdr is None:
        raise SystemExit("steps: not found")
    indent = re.match(r'^(\s*)', ls[steps_hdr]).group(1) + "  "
    insert_at = steps_hdr+1
    new = ls[:insert_at] + [
        f"{indent}- name: Score board",
        f"{indent}  run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml"
    ] + ls[insert_at:]
    return new, "APPENDED"

idxs = find_steps_indices(lines)
target = None; k_target = None
patterns = [
    r'code_cli_run_edge_sheet_v1\.py',
    r'emit[_\-]?edge[_\-]?sheet',
    r'edge[_\-]?sheet.*\.py'
]
for k in range(len(idxs)):
    s,e = step_bounds(lines, idxs, k)
    block = "\n".join(lines[s:e])
    if any(re.search(p, block) for p in patterns):
        target = (s,e); k_target = k; break

if target:
    s,e = target
    name_indent = re.match(r'^(\s*)', lines[s]).group(1)
    lines[s] = f"{name_indent}- name: Score board"
    run_replaced = False
    for i in range(s+1, e):
        m = re.match(r'^(\s*)run:\s*(.+)$', lines[i])
        if m:
            lines[i] = f"{m.group(1)}run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml"
            run_replaced = True
            break
    if not run_replaced:
        lines.insert(s+1, f"{name_indent}  run: python3 scripts/score_board.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml")
    wf.write_text("\n".join(lines))
    print("OK")
else:
    lines2, status = ensure_scorer_step(lines)
    wf.write_text("\n".join(lines2))
    print(status)
