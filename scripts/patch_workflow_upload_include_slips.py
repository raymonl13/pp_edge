#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
upload=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]):
        upload=k; break
if upload is None:
    print("UPLOAD_NOT_FOUND"); exit(1)
s,e=bounds(upload)
# find the "path:" block under Upload
path_line=None
for j in range(s+1,e):
    if re.match(r'^\s*path:\s*\|', L[j]):
        path_line=j; break
if path_line is None:
    print("UPLOAD_PATH_BLOCK_NOT_FOUND"); exit(1)
indent=re.match(r'^(\s*)', L[path_line]).group(1)+"  "
want=["slips.json","alloc_slips.csv"]
present=set()
j=path_line+1
while j<e and (L[j].startswith(indent) or L[j].strip()==""):
    line=L[j].strip()
    if line in want: present.add(line)
    j+=1
to_add=[w for w in want if w not in present]
for w in to_add:
    L.insert(j, indent+w)
wf.write_text("\n".join(L))
print("OK")
