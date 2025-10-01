#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
t=wf.read_text(); lines=t.splitlines()
idx=[i for i,l in enumerate(lines) if re.match(r'^\s*-\s*name:\s*',l)]
qa=None
for i in idx:
    if re.search(r'^\s*-\s*name:\s*QA\+Alloc\s*$', lines[i]): qa=i; break
if qa is None: print("not_found"); raise SystemExit(0)
end=next((j for j in idx if j>qa), len(lines))
ins=end
for j in range(qa+1,end):
    if re.search(r'^\s*-\s*name:\s*Relax QA on SYNTH\s*$', lines[j]): print("already"); raise SystemExit(0)
indent=re.match(r'^(\s*)',lines[qa]).group(1)
runindent=indent+"  "
lines.insert(ins, runindent+"- name: Relax QA on SYNTH")
lines.insert(ins+1, runindent+"  run: python3 scripts/qa_relax_on_synth.py")
wf.write_text("\n".join(lines))
print("OK")
