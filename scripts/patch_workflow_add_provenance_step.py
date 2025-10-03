#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e

score_k=None; diag_k=None; build_k=None
for k in range(len(idx)):
    nm=L[idx[k]].strip()
    if re.search(r'^- name:\s*Score board\s*$', nm): score_k=k
    if re.search(r'^- name:\s*Diagnose slips\s*$', nm): diag_k=k
    if re.search(r'^- name:\s*Build slips\s*$', nm): build_k=k
if build_k is None: print("BUILD_STEP_NOT_FOUND"); exit(0)

ins=idx[build_k]  # insert right before Build slips
ind=re.match(r'^(\s*)', L[idx[build_k]]).group(1)
step=[
f"{ind}- name: Show builder provenance",
f"{ind}  if: always()",
f"{ind}  run: |",
f"{ind}    set -euo pipefail",
f"{ind}    echo '=== BUILDER PROVENANCE ==='",
f"{ind}    python3 - <<'PPY'",
f"{ind}    from pathlib import Path",
f"{ind}    p=Path('scripts/build_slips.py'); s=p.read_text()",
f"{ind}    sig='unknown'",
f"{ind}    for ln in s.splitlines():",
f"{ind}        if ln.startswith('BUILDER_SIG') and '=' in ln:",
f"{ind}            sig=ln.split('=',1)[1].strip().strip('\"\\'')",
f"{ind}            break",
f"{ind}    import hashlib; h=hashlib.sha256(p.read_bytes()).hexdigest()[:16]",
f"{ind}    print('BUILDER_SIG='+sig)",
f"{ind}    print('BUILDER_SHA256='+h)",
f"{ind}    PPY",
f"{ind}    echo '--- scripts/build_slips.py (head) ---'; head -n 40 scripts/build_slips.py || true",
]
L[ins:ins]=step
wf.write_text("\n".join(L)); print("OK")
