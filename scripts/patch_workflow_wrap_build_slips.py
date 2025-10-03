#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

build_k=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$', L[idx[k]]):
        build_k=k; break
if build_k is None: print("BUILD_STEP_NOT_FOUND"); exit(0)

s,e=blk(build_k)
run_i=None
for j in range(s+1,e):
    if re.match(r'^\s*run:\s*(\|.*|>.*|.*)$', L[j]): run_i=j; break

ind=re.match(r'^(\s*)', L[idx[build_k]]).group(1)
body=[
f"{ind}  run: |",
f"{ind}    set -xeuo pipefail",
f'{ind}    echo "=== BUILD SLIPS ENV ==="',
f'{ind}    echo "PYTHON: $(python3 -V)"',
f'{ind}    echo "DAY=${{DAY:-}}"',
f'{ind}    ls -l || true',
f'{ind}    if [ -z "${{DAY:-}}" ]; then DAY="$(date -u +%F)"; fi',
f'{ind}    ES="edge_sheet_${{DAY}}.csv"; echo "--- HEAD of $ES ---"; head -n 6 "$ES" 2>/dev/null || echo "missing $ES"',
f"{ind}    export PYTHONFAULTHANDLER=1",
f'{ind}    python3 -X dev -W error scripts/build_slips.py "$DAY" --cfg config_pp_edge_v6.8.yaml 1>builder_stdout.log 2>builder_stderr.log',
f'{ind}    rc=$?; echo "BUILD_SLIPS_RC=$rc" | tee -a run_meta.txt; test $rc -eq 0'
]
if run_i is None:
    L.insert(e, body[0]); L[e+1:e+1]=body[1:]
else:
    m=re.match(r'^(\s*)', L[run_i])
    j=run_i+1
    while j<e and (L[j].startswith(m.group(1)+"  ") or L[j].strip()==""):
        j+=1
    del L[run_i:j]
    L[run_i:run_i]=body

wf.write_text("\n".join(L)); print("OK")
