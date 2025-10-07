import sys, yaml, pathlib
paths=[".github/workflows/nightly_edge_sheet.yml",".github/workflows/nightly_edge_sheet.yaml",".github/workflows/manual_edge_sheet_e2e.yml",".github/workflows/manual_edge_sheet.yml"]
def load_first():
    for p in paths:
        fp=pathlib.Path(p)
        if fp.exists():
            return fp
    raise SystemExit(2)
def has_step(steps,name):
    for s in steps:
        if isinstance(s,dict) and s.get("name")==name:
            return True
    return False
wf_path=load_first()
data=yaml.safe_load(wf_path.read_text())
jobs=data.get("jobs",{})
changed=False
for jname,job in jobs.items():
    steps=job.get("steps",[])
    if not isinstance(steps,list):
        continue
    if has_step(steps,"Outcomes rollup"):
        continue
    step={"name":"Outcomes rollup","if":"${{ always() }}","shell":"bash","run":'PY_BIN="${{ env.PY_BIN:-python3 }}"\n"$PY_BIN" scripts/outcomes_rollup.py'}
    steps.append(step)
    job["steps"]=steps
    jobs[jname]=job
    changed=True
    break
if changed:
    data["jobs"]=jobs
    wf_path.write_text(yaml.safe_dump(data,sort_keys=False))
    print("patched",str(wf_path))
else:
    print("nochange",str(wf_path))
