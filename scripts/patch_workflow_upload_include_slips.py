#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path, re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
upload=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload=k; break
if upload is None: print("UPLOAD_NOT_FOUND"); exit(1)
s,e=blk(upload)
path=None
for j in range(s+1,e):
    if re.match(r'^\s*path:\s*\|', L[j]): path=j; break
if path is None: print("UPLOAD_PATH_NOT_FOUND"); exit(1)
indent=re.match(r'^(\s*)', L[path]).group(1)+"  "
present=set(); j=path+1
while j<e and (L[j].startswith(indent) or L[j].strip()==""):
    present.add(L[j].strip()); j+=1
for want in ["slips.json","alloc_slips.csv"]:
    if want not in present: L.insert(j, indent+want)
wf.write_text("\n".join(L)); print("OK")
