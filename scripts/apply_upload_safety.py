#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
t=wf.read_text()
L=t.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def step_bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
qa=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*QA\+Alloc\s*$',L[idx[k]]): qa=k
if qa is None: print("QA_NOT_FOUND"); exit(1)
sqa,eqa=step_bounds(qa)
ins=eqa
for k in range(qa+1,len(idx)):
    if re.search(r'^\s*-\s*name:\s*QA gate\s*$',L[idx[k]]):
        ins=idx[k]; break
indent=re.match(r'^(\s*)',L[sqa]).group(1)+"  "
exists=False
for i in range(sqa,ins):
    if re.search(r'^\s*-\s*name:\s*Ensure pre-upload placeholders\s*$',L[i]): exists=True
if not exists:
    body=[
        f"{indent}- name: Ensure pre-upload placeholders",
        f"{indent}  if: always()",
        f"{indent}  run: |",
        f"{indent}    set -euo pipefail",
        f"{indent}    if [ -z \"${{ env.DAY }}\" ]; then DAY=\"$(date -u +%F)\"; else DAY=\"${{ env.DAY }}\"; fi",
        f"{indent}    f=\"edge_sheet_${{DAY}}.csv\"; test -f \"$f\" || printf \"player,game_id,p_hit,edge_pp,tier,slip_type\\n\" > \"$f\"",
        f"{indent}    meta=\"run_meta.txt\"; test -f \"$meta\" || printf \"CSV_ROWS=0\\n\" > \"$meta\"",
        f"{indent}    test -f qa_report.json || printf '{{}}' > qa_report.json",
        f"{indent}    test -f qa_report.csv || printf 'severity,msg\\n' > qa_report.csv",
        f"{indent}    test -f alloc_summary.csv || printf 'player,game_id,tier,slip_type,stake\\n' > alloc_summary.csv",
    ]
    L[ins:ins]=body
    ins+=len(body)
upload_found=False
for i in range(ins,len(L)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$',L[i]):
        upload_found=True
        s=i; j=i+1
        has_if=False
        while j<len(L) and (not re.match(r'^\s*-\s*name:\s*',L[j])):
            m=re.match(r'^(\s*)if:\s*',L[j])
            if m: L[j]=f"{m.group(1)}if: always()"; has_if=True; break
            j+=1
        if not has_if:
            L.insert(i+1, indent+"if: always()")
        break
if not upload_found:
    body=[
        f"{indent}- name: Upload",
        f"{indent}  if: always()",
        f"{indent}  uses: actions/upload-artifact@v4",
        f"{indent}  with:",
        f"{indent}    name: qa_alloc_auto",
        f"{indent}    path: |",
        f"{indent}      edge_sheet_*.csv",
        f"{indent}      qa_report.json",
        f"{indent}      qa_report.csv",
        f"{indent}      alloc_summary.csv",
        f"{indent}      run_meta.txt",
        f"{indent}      .artifact_marker",
        f"{indent}    if-no-files-found: ignore",
        f"{indent}    compression-level: 6",
        f"{indent}    overwrite: false",
    ]
    L[ins:ins]=body
wf.write_text("\n".join(L))
print("OK")
