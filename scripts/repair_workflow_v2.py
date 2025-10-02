#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
step_indent=re.match(r'^(\s*)', L[idx[0]]).group(1) if idx else "  "

# swap emitter -> score
cmd_score='python3 scripts/score_board.py "$DAY" --cfg config_pp_edge_v6.8.yaml'
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Emit CSV from board\s*$', L[idx[k]]):
        s,e=blk(k); ind=re.match(r'^(\s*)',L[idx[k]]).group(1); L[idx[k]]=f"{ind}- name: Score board"
        replaced=False
        for j in range(s+1,e):
            m=re.match(r'^(\s*)run:\s*(\|.*|>.*|.*)$', L[j])
            if m:
                ind2=m.group(1); j2=j+1
                while j2<e and (L[j2].startswith(ind2+"  ") or L[j2].strip()==""): j2+=1
                del L[j:j2]; L.insert(j, f"{ind2}run: {cmd_score}"); replaced=True; break
        if not replaced: L.insert(s+1, f"{ind}  run: {cmd_score}")
        break

# refresh step indices
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]

# Upload & QA gate positions
upload_k=None; qagate_k=None
for k in range(len(idx)):
    n=L[idx[k]].strip()
    if re.search(r'^- name:\s*Upload\s*$', n): upload_k=k
    if re.search(r'^- name:\s*QA gate\s*$', n): qagate_k=k

# Build slips present?
need_build=True
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$', L[idx[k]]): need_build=False

if need_build:
    insert_at = idx[upload_k] if upload_k is not None else (idx[qagate_k] if qagate_k is not None else len(L))
    ind=step_indent
    L[insert_at:insert_at]=[f"{ind}- name: Build slips", f'{ind}  run: python3 scripts/build_slips.py "$DAY" --cfg config_pp_edge_v6.8.yaml']

# refresh indices
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]

# Ensure Upload exists and includes slip artifacts
upload_k=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload_k=k; break

if upload_k is None:
    insert_at = idx[qagate_k] if qagate_k is not None else len(L)
    ind=step_indent
    L[insert_at:insert_at]=[
        f"{ind}- name: Upload",
        f"{ind}  uses: actions/upload-artifact@v4",
        f"{ind}  with:",
        f"{ind}    name: qa_alloc_auto",
        f"{ind}    path: |",
        f"{ind}      edge_sheet_*.csv",
        f"{ind}      qa_report.json",
        f"{ind}      qa_report.csv",
        f"{ind}      alloc_summary.csv",
        f"{ind}      run_meta.txt",
        f"{ind}      .artifact_marker",
        f"{ind}      slips.json",
        f"{ind}      alloc_slips.csv",
        f"{ind}    if-no-files-found: warn",
        f"{ind}    compression-level: 6",
        f"{ind}    overwrite: false",
    }
else:
    s,e=blk(upload_k)
    path=None
    for j in range(s+1,e):
        if re.match(r'^\s*path:\s*\|', L[j]): path=j; break
    if path is not None:
        ind=re.match(r'^(\s*)',L[path]).group(1)+"  "
        present=set(); j=path+1
        while j<e and (L[j].startswith(ind) or L[j].strip()==""): present.add(L[j].strip()); j+=1
        for w in ["slips.json","alloc_slips.csv"]:
            if w not in present: L.insert(j, ind+w)

# relax fallback placeholders step
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Fallback meta and CSV \(force placeholders\)\s*$', L[idx[k]]):
        s,e=blk(k); found=False
        for j in range(s+1,e):
            m=re.match(r'^(\s*)continue-on-error:\s*', L[j])
            if m: L[j]=f"{m.group(1)}continue-on-error: true"; found=True; break
        if not found:
            ind=re.match(r'^(\s*)',L[idx[k]]).group(1)+"  "
            L.insert(s+1, f"{ind}continue-on-error: true")
        break

wf.write_text("\n".join(L))
print("OK")
