#!/usr/bin/env python3
import argparse, sys, os, yaml
ROLLUP_NAME="Outcomes rollup"
UPLOAD_NAME="Upload outcomes_rollup"
def _has_step(steps,name):
    for s in steps:
        if isinstance(s,dict) and s.get("name")==name: return True
    return False
def _edge_upload_idx(steps):
    for i,s in enumerate(steps):
        if not isinstance(s,dict): continue
        if str(s.get("uses","")).startswith("actions/upload-artifact@"):
            w=s.get("with",{}); n=str(w.get("name",""))
            if "edge_sheet" in n or "edgesheet" in n or "edge_sheet_" in n: return i
    return -1
def ensure(steps):
    if not _has_step(steps,ROLLUP_NAME):
        cmd="\n".join([
            "${PY:-python3} -m pip install -q pandas",
            "${PY:-python3} scripts/ci_outcomes_backfill.py --days 14 > outcomes_dates.txt",
            "while read -r d; do ${PY:-python3} scripts/ci_make_training_table.py --date \"$d\" || true; done < outcomes_dates.txt",
            "${PY:-python3} scripts/outcomes_rollup.py --days 30"
        ])
        slot=_edge_upload_idx(steps)
        block={"name":ROLLUP_NAME,"if":"always()","continue-on-error":True,"run":cmd}
        if slot>=0: steps.insert(slot+1,block)
        else: steps.append(block)
    if not _has_step(steps,UPLOAD_NAME):
        steps.append({"name":UPLOAD_NAME,"if":"always()","continue-on-error":True,"uses":"actions/upload-artifact@v4","with":{"name":"outcomes_rollup","path":"outcomes_rollup","if-no-files-found":"warn"}})
    return steps
def patch(path):
    wf=yaml.safe_load(open(path))
    jobs=wf.get("jobs",{})
    if not jobs: return False
    for k,job in jobs.items():
        if "steps" in job:
            job["steps"]=ensure(list(job["steps"]))
            wf["jobs"][k]=job
            break
    yaml.safe_dump(wf,open(path,"w"),sort_keys=False)
    return True
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--path",default=".github/workflows/nightly_edge_sheet.yml")
    args=ap.parse_args()
    ok=patch(args.path)
    print(f"patched={ok} file={args.path}")
    sys.exit(0 if ok else 1)
if __name__=="__main__": main()
