#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

build_k=None; upload_k=None
for k in range(len(idx)):
    name=L[idx[k]].strip()
    if re.search(r'^- name:\s*Build slips\s*$', name): build_k=k
    if re.search(r'^- name:\s*Upload\s*$', name): upload_k=k
if build_k is None:
    print("BUILD_STEP_NOT_FOUND"); exit(0)

# Insert Allocate stakes right after Build slips
_,be=blk(build_k)
ind=re.match(r'^(\s*)', L[idx[build_k]]).group(1)
step=[f"{ind}- name: Allocate stakes", f'{ind}  if: always()', f'{ind}  run: python3 scripts/allocate_stakes.py "$DAY" --cfg config_pp_edge_v6.8.yaml']
L[be:be]=step

# Ensure Upload includes alloc_slips_with_stakes.csv
if upload_k is not None:
    s,e=blk(upload_k)
    path=None
    for j in range(s+1,e):
        if re.match(r'^\s*path:\s*\|', L[j]): path=j; break
    if path is not None:
        indent=re.match(r'^(\s*)', L[path]).group(1)+"  "
        present=set(); j=path+1
        while j<e and (L[j].startswith(indent) or L[j].strip()==""):
            present.add(L[j].strip()); j+=1
        want="alloc_slips_with_stakes.csv"
        if want not in present:
            L.insert(j, indent+want)

wf.write_text("\n".join(L)); print("OK")
