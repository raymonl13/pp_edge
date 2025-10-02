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
    if re.search(r'^\s*-\s*name:\s*Upload\s*$',L[idx[k]]): upload=idx[k]; break
if upload is None: print("UPLOAD_NOT_FOUND"); exit(1)
exists=False
for j in range(idx[0], upload):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$',L[j]): exists=True; break
if not exists:
    ind=re.match(r'^(\s*)',L[upload]).group(1)
    ins=upload
    body=[f"{ind}- name: Build slips", f"{ind}  run: python3 scripts/build_slips.py \"$DAY\" --cfg config_pp_edge_v6.8.yaml"]
    L[ins:ins]=body
wf.write_text("\n".join(L))
print("OK")
