#!/usr/bin/env python3
import argparse,datetime,json,sys
from pathlib import Path
from code_utils_slipqa_v2 import load_edge_sheet,run_qa,_load_yaml,QA_RULES_VERSION,resolve_day
from code_utils_allocator_v2 import allocate,ALLOC_VERSION,resolve_day as resolve_day_alloc
def _write_csv(path:Path,rows,header):
    import csv
    with path.open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=header)
        w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in header})
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day",nargs="?")
    ap.add_argument("--cfg",default="config_pp_edge_v6.8.yaml")
    ap.add_argument("--tz",default="America/Los_Angeles")
    args=ap.parse_args()
    day=resolve_day(args.day,args.tz)
    edge_csv=Path(f"edge_sheet_{day}.csv")
    try:
        if not edge_csv.exists():
            Path("qa_report.json").write_text(json.dumps({"state":"FAIL","rules_version":QA_RULES_VERSION,"issues":[{"severity":"FAIL","msg":"edge_csv_missing"}]},indent=2))
            Path("qa_report.csv").write_text("severity,msg\nFAIL,edge_csv_missing\n")
            Path("alloc_summary.csv").write_text("player,game_id,tier,slip_type,stake\n")
            with open("run_meta.txt","a") as f: f.write(f"QA_STATE=FAIL ALLOC_STATE=WARN QA_RULES_VERSION={QA_RULES_VERSION} ALLOC_VERSION={ALLOC_VERSION}\n")
            print("FAIL"); print("WARN"); return
        cfg=_load_yaml(Path(args.cfg))
        rows=load_edge_sheet(edge_csv)
        qa=run_qa(rows,cfg)
        Path("qa_report.json").write_text(json.dumps(qa,indent=2,sort_keys=True))
        _write_csv(Path("qa_report.csv"),qa.get("issues",[]),header=["severity","msg"])
        qa_state=qa.get("state","UNKNOWN"); print(qa_state)
        out_rows=allocate(rows,cfg)
        _write_csv(Path("alloc_summary.csv"),out_rows,header=["player","game_id","tier","slip_type","stake"])
        alloc_state="OK" if any(float(r.get("stake") or 0)>0 for r in out_rows) else "WARN"; print(alloc_state)
        rows_count=len(rows)
        with open("run_meta.txt","a") as f:
            f.write(f"QA_STATE={qa_state} ALLOC_STATE={alloc_state} QA_RULES_VERSION={QA_RULES_VERSION} ALLOC_VERSION={ALLOC_VERSION} CSV_ROWS={rows_count}\n")
    except Exception as e:
        Path("qa_report.json").write_text(json.dumps({"state":"FAIL","rules_version":QA_RULES_VERSION,"issues":[{"severity":"FAIL","msg":f"exception:{type(e).__name__}:{e}"}]},indent=2))
        Path("qa_report.csv").write_text("severity,msg\nFAIL,exception\n")
        with open("run_meta.txt","a") as f: f.write(f"QA_STATE=FAIL ALLOC_STATE=WARN QA_RULES_VERSION={QA_RULES_VERSION} ALLOC_VERSION={ALLOC_VERSION}\n")
        print("FAIL"); print("WARN")
    finally:
        sys.exit(0)
if __name__=="__main__": main()
