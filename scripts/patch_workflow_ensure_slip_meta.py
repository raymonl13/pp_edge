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
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload=k; break
if upload is None: print("UPLOAD_NOT_FOUND"); exit(1)
ins=idx[upload]
ind=re.match(r'^(\s*)', L[upload]).group(1)
step=[f"{ind}- name: Ensure slip meta lines",
      f"{ind}  run: |",
      f"{ind}    set -euo pipefail",
      f'{ind}    m="run_meta.txt"',
      f'{ind}    need=(SLIPS_BUILT SLIP_KEYS_METHOD SLIP_KEYS_OBSERVED SLIP_EV_METHOD)',
      f'{ind}    miss=0',
      f'{ind}    for k in "${{need[@]}}"; do grep -q "^$k=" "$m" 2>/dev/null || miss=1; done',
      f'{ind}    if [ "$miss" -eq 1 ]; then python3 scripts/build_slips.py "$DAY" --cfg config_pp_edge_v6.8.yaml; fi']
L[ins:ins]=step
wf.write_text("\n".join(L)); print("OK")
