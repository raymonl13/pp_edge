#!/usr/bin/env python3
import argparse, datetime, json, os, yaml, pandas as pd, joblib
from code_core_pp_edge_core_v6_7_v6 import run_pipeline

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date")
    p.add_argument("--cfg", default="config_pp_edge_v6.8.yaml")
    args = p.parse_args()
    tgt  = args.date or (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    board = f"data/pricefix_{tgt}.json"
    if not os.path.exists(board):
        raise SystemExit(f"board not found: {board}")

    cfg   = yaml.safe_load(open(args.cfg))
    legs  = json.load(open(board))
    slips = run_pipeline(legs, cfg)

    out   = f"edge_sheet_{tgt}.csv"
    pd.DataFrame(slips).to_csv(out, index=False)
    print(f"edge sheet written → {out} rows:{len(slips)}")

if __name__ == "__main__":
    main()
