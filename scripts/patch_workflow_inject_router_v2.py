#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, sys

wf = Path(".github/workflows/manual_edge_sheet_e2e.yml")
if not wf.exists():
    print("ERROR: workflow not found:", wf); sys.exit(1)

txt = wf.read_text()
L = txt.splitlines()
idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]

def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
def find_step(rx: str):
    for k in range(len(idx)):
        if re.search(rx, L[idx[k]]): return k
    return None

score_k = find_step(r'^\s*-\s*name:\s*Score board\s*$')
if score_k is None:
    print("ERROR: 'Score board' step not found"); sys.exit(1)

s,e = blk(score_k)
ind = re.match(r'^(\s*)', L[idx[score_k]]).group(1)
prov = [
f"{ind}- name: Show router provenance",
f"{ind}  if: always()",
f"{ind}  run: |",
f"{ind}    set -euo pipefail",
f"{ind}    python3 - <<'PPY'",
f"{ind}    from pathlib import Path, hashlib",
f"{ind}    p=Path('scripts/route_fetch.py')",
f"{ind}    sha=hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else 'missing'",
f"{ind}    print('ROUTER_SIG='+sha)",
f"{ind}    print('--- head scripts/route_fetch.py ---')",
f"{ind}    print('\\n'.join(p.read_text().splitlines()[:30]) if p.exists() else 'missing')",
f"{ind}    PPY",
]
L[s:s] = prov

idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
score_k = find_step(r'^\s*-\s*name:\s*Score board\s*$')
s,e = blk(score_k)
route = [
f"{ind}- name: Route fetch (Session 7)",
f"{ind}  env:",
f"{ind}    ROUTER_API_KEY: ${{{{ secrets.ROUTER_API_KEY }}}}",
f"{ind}  run: |",
f"{ind}    set -xeuo pipefail",
f"{ind}    mkdir -p data/logs",
f"{ind}    export PYTHONFAULTHANDLER=1",
f"{ind}    python -X dev -W error scripts/route_smoke.py || true",
f"{ind}    python -X dev -W error scripts/route_fetch.py 1>data/logs/router_stdout.log 2>data/logs/router_stderr.log",
]
L[s:s] = route

idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
upload_k = find_step(r'^\s*-\s*name:\s*Upload.*artifact')
merge_block = [
f"{ind}- name: Merge router summary into run_debug",
f"{ind}  if: always()",
f"{ind}  run: |",
f"{ind}    set -euo pipefail",
f"{ind}    cp data/logs/route_debug.json run_debug_router.json || true",
f"{ind}    cat data/logs/router_summary.txt >> run_debug.txt 2>/dev/null || true",
]
if upload_k is not None:
    s,e = blk(upload_k)
    L[s:s] = merge_block
else:
    score_k = find_step(r'^\s*-\s*name:\s*Score board\s*$')
    s,e = blk(score_k)
    L[s:s] = merge_block

idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
upload_k = find_step(r'^\s*-\s*name:\s*Upload.*artifact')
if upload_k is not None:
    s,e = blk(upload_k)
    path_line=None
    for j in range(s+1, e):
        if re.match(r'^\s*path:\s*\|', L[j]): path_line=j; break
    if path_line is not None:
        indent = re.match(r'^(\s*)', L[path_line]).group(1) + "  "
        present=set(); j=path_line+1
        while j<e and (L[j].startswith(indent) or L[j].strip()==""):
            present.add(L[j].strip()); j+=1
        want = {
            "data/logs/router_stdout.log",
            "data/logs/router_stderr.log",
            "data/logs/route_debug.json",
            "run_debug_router.json",
        }
        for w in sorted(want):
            if w not in present:
                L.insert(j, indent + w); j += 1

txt = "\n".join(L)
txt = re.sub(r'(?ms)^\s*workflow_dispatch:.*?(?=^\S|\Z)', '', txt)
wf.write_text(txt)
print("OK")
