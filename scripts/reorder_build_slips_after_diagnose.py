#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()

# index steps
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

build_k=None; diag_k=None
for k in range(len(idx)):
    n=L[idx[k]].strip()
    if re.search(r'^- name:\s*Build slips\s*$', n): build_k=k
    if re.search(r'^- name:\s*Diagnose slips\s*$', n): diag_k=k

if diag_k is None:
    print("MISSING_DIAGNOSE"); exit(0)
if build_k is None:
    print("MISSING_BUILD"); exit(0)

# capture Build slips block
bs,be=blk(build_k)
build_block=L[bs:be]
# remove it from current location
del L[bs:be]

# recompute indices after removal
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def blk2(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

# find Diagnose again
diag_k=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Diagnose slips\s*$', L[idx[k]]): diag_k=k; break
_,de=blk2(diag_k)

# insert Build slips immediately after Diagnose block
L[de:de]=build_block

wf.write_text("\n".join(L))
print("OK")
