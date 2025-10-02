#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); lines=txt.splitlines()
idx=[i for i,l in enumerate(lines) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(lines); return s,e
def ensure_always(name):
    for k,i in enumerate(idx):
        if re.search(rf'^\s*-\s*name:\s*{name}\s*$',lines[i]):
            s,e=bounds(k); found=False
            for j in range(s+1,e):
                m=re.match(r'^(\s*)if:\s*(.+)$',lines[j])
                if m: lines[j]=f"{m.group(1)}if: always()"; found=True; break
            if not found:
                ind=re.match(r'^(\s*)',lines[i]).group(1)+"  "
                lines.insert(s+1,f"{ind}if: always()")
            return
ensure_always("Artifact marker")
ensure_always("Upload")
Path(".github/workflows/manual_edge_sheet_e2e.yml").write_text("\n".join(lines)); print("OK")
