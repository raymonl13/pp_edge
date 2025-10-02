#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
score_k=None; build_k=None; upload_k=None
for k in range(len(idx)):
    n=L[idx[k]].strip()
    if re.search(r'^- name:\s*Score board\s*$', n): score_k=k
    if re.search(r'^- name:\s*Build slips\s*$', n): build_k=k
    if re.search(r'^- name:\s*Upload\s*$', n): upload_k=k
if score_k is None or build_k is None:
    print("MISSING_SCORE_OR_BUILD"); exit(0)
_,e=blk(score_k); ins=e
ind=re.match(r'^(\s*)', L[idx[score_k]]).group(1)
# add diagnose if missing
exists=False
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Diagnose slips\s*$', L[idx[k]]): exists=True
if not exists:
    L[ins:ins]=[f"{ind}- name: Diagnose slips", f'{ind}  run: python3 scripts/diagnose_slips.py "$DAY" --cfg config_pp_edge_v6.8.yaml']
# ensure upload includes diagnosis files
if upload_k is not None:
    s,e=blk(upload_k)
    path=None
    for j in range(s+1,e):
        if re.match(r'^\s*path:\s*\|', L[j]): path=j; break
    if path is not None:
        ind2=re.match(r'^(\s*)', L[path]).group(1)+"  "
        present=set(); j=path+1
        while j<e and (L[j].startswith(ind2) or L[j].strip()==""):
            present.add(L[j].strip()); j+=1
        for want in ["slip_diag.json","slip_diag.txt"]:
            if want not in present: L.insert(j, ind2+want)
wf.write_text("\n".join(L)); print("OK")
