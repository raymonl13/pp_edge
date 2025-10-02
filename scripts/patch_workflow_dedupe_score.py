#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
score_steps=[k for k in range(len(idx)) if re.search(r'^\s*-\s*name:\s*Score board\s*$', L[idx[k]])]
if len(score_steps)>1:
  # keep the first, remove subsequent
  for k in reversed(score_steps[1:]):
    s,e=bounds(k)
    del L[s:e]
wf.write_text("\n".join(L))
print("OK")
