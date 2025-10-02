#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
pre=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Ensure pre-upload placeholders\s*$', L[idx[k]]):
        pre=k; break
if pre is None:
    print("PREUPLOAD_NOT_FOUND"); exit(0)
s,e=bounds(pre)
# find 'run: |' of that step
run=None
for j in range(s+1,e):
    if re.match(r'^\s*run:\s*\|', L[j]): run=j; break
if run is None:
    print("PREUPLOAD_RUN_NOT_FOUND"); exit(0)
indent=re.match(r'^(\s*)', L[run]).group(1)+"  "
body=[
    'test -f slips.json || printf \'{"day":"%s","slips":[]}\\n\' "$(date -u +%F)" > slips.json',
    "test -f alloc_slips.csv || printf 'slip_id,slip_type,size,ev,ev_method,players,games\\n' > alloc_slips.csv",
]
# insert just before next step start
insert_at=run+1
while insert_at<e and (L[insert_at].startswith(indent) or L[insert_at].strip()==""):
    insert_at+=1
for line in body[::-1]:
    L.insert(insert_at, indent+line)
wf.write_text("\n".join(L))
print("OK")
