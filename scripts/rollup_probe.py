#!/usr/bin/env python3
import argparse, datetime as dt, json, os, pandas as pd, sys
def parse_args():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("--day"); p.add_argument("--out")
    known, unknown = p.parse_known_args()
    day = known.day; out = known.out
    pos = [u for u in unknown if not u.startswith("-")]
    if day is None and pos: day = pos[0]
    if out is None and len(pos) > 1: out = pos[1]
    if day is None: day = dt.date.today().isoformat()
    if out is None: out = f"rollup_probe_{day}.json"
    return day, out
def main():
    day, out = parse_args()
    edge = f"edge_sheet_{day}.csv"
    rows = 0
    if os.path.exists(edge):
        try:
            df = pd.read_csv(edge)
            rows = int(len(df))
        except Exception:
            rows = 0
    payload = {"day": day, "edge_rows": rows}
    with open(out, "w") as f: json.dump(payload, f)
    print(out)
if __name__=="__main__": sys.exit(main())
