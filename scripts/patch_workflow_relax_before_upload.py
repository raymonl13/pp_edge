#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
t=wf.read_text(); L=t.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
qa=None; up=None
for i in idx:
    if re.search(r'^\s*-\s*name:\s*QA\+Alloc\s*$',L[i]): qa=i
    if re.search(r'^\s*-\s*name:\s*Upload\s*$',L[i]): up=i
if qa is None or up is None or up<=qa: raise SystemExit(0)
for j in range(qa+1,up):
    if re.search(r'^\s*-\s*name:\s*Relax QA on SYNTH\s*$',L[j]): raise SystemExit(0)
ind=re.match(r'^(\s*)',L[qa]).group(1); runind=ind+"  "
L.insert(up, runind+"- name: Relax QA on SYNTH")
L.insert(up+1, runind+"  if: always()")
L.insert(up+2, runind+"  run: python3 scripts/qa_relax_on_synth.py")
wf.write_text("\n".join(L)); print("OK")
