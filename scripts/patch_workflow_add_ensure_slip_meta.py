#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
build=None; upload=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$', L[idx[k]]): build=k
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload=k
if build is None or upload is None: print("MISSING_BUILD_OR_UPLOAD"); exit(0)
s,e=blk(build); ins=e
ind=re.match(r'^(\s*)', L[idx[build]]).group(1)
exists=False
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Ensure slip meta\s*$', L[idx[k]]): exists=True
if not exists:
    L[ins:ins]=[f"{ind}- name: Ensure slip meta", f'{ind}  run: python3 scripts/ensure_slip_meta.py']
wf.write_text("\n".join(L)); print("OK")
