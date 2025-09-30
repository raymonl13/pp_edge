#!/usr/bin/env python3
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
s=wf.read_text()
if "Run QA + Alloc" in s and "Upload QA/Alloc artifacts" in s:
    print("Workflow already patched."); raise SystemExit(0)
block=("""\
      - name: Install deps (qa_alloc)
        shell: bash
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml pandas

      - name: Run QA + Alloc
        shell: bash
        env:
          SLATE_TZ: America/Los_Angeles
        run: |
          if [ -n "${DAY:-}" ]; then python3 scripts/run_qa_alloc.py "$DAY" --cfg config_pp_edge_v6.8.yaml --tz "$SLATE_TZ" || true; else python3 scripts/run_qa_alloc.py --cfg config_pp_edge_v6.8.yaml --tz "$SLATE_TZ" || true; fi

      - name: Upload QA/Alloc artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: qa_alloc_${{ github.run_number }}
          path: |
            qa_report.json
            qa_report.csv
            alloc_summary.csv
            run_meta.txt
          if-no-files-found: warn
""")
m=re.search(r'(?m)^\s*- name:\s*Summarize meta\s*$',s)
if m:
    idx=m.end(); patched=s[:idx]+"\n"+block+s[idx:]
else:
    m2=re.search(r'(?m)^\s*- name:\s*actionlint\s*$',s)
    if m2: idx=m2.start(); patched=s[:idx]+block+s[idx:]
    else: patched=s+"\n"+block
wf.write_text(patched)
print("Patched manual_edge_sheet_e2e.yml")
