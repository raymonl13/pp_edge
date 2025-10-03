#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

for title in (r'Ensure slip meta', r'Run debug report'):
    for k in range(len(idx)):
        if re.search(r'^\s*-\s*name:\s*'+title+r'\s*$', L[idx[k]]):
            s,e=blk(k); has=False
            for j in range(s+1,e):
                m=re.match(r'^(\s*)if:\s*(.+)$', L[j])
                if m:
                    L[j]=f"{m.group(1)}if: always()"; has=True; break
            if not has:
                ind=re.match(r'^(\s*)', L[idx[k]]).group(1)+"  "
                L.insert(s+1, f"{ind}if: always()")
            break

wf.write_text("\n".join(L)); print("OK")
