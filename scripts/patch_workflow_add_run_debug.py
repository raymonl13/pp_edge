#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

upload_k=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload_k=k; break
if upload_k is None:
    print("UPLOAD_NOT_FOUND"); exit(1)

# insert 'Run debug report' before Upload
ins=idx[upload_k]
ind=re.match(r'^(\s*)', L[idx[upload_k]]).group(1)
step=[f"{ind}- name: Run debug report", f'{ind}  run: python3 scripts/run_debug_report.py']
L[ins:ins]=step

# ensure Upload includes run_debug files and builder debug
s,e=blk(upload_k+1)  # upload moved down by insertion
path=None
for j in range(s+1,e):
    if re.match(r'^\s*path:\s*\|', L[j]): path=j; break
if path is not None:
    ind2=re.match(r'^(\s*)', L[path]).group(1)+"  "
    present=set(); j=path+1
    while j<e and (L[j].startswith(ind2) or L[j].strip()==""):
        present.add(L[j].strip()); j+=1
    for want in ["run_debug.txt","run_debug.json","slip_builder_debug.json"]:
        if want not in present: L.insert(j, ind2+want)

wf.write_text("\n".join(L)); print("OK")
