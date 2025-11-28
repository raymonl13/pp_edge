#!/usr/bin/env python3
import argparse, csv
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--budget", type=float, default=100.0)
    ap.add_argument("--stake",  type=float, default=10.0)
    args = ap.parse_args()

    day = args.day
    in_csv  = Path("runs")/"nba"/day/f"slips_nba_v0.csv"
    out_csv = Path("runs")/"nba"/day/f"slips_nba_v0_sized.csv"
    if not in_csv.exists():
        print(f"[size_bankroll_v0] no slips CSV present: {in_csv}")
        return

    with in_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or ["slip_type","edge_pp","stake_total","num_legs","legs_summary"]

    if not rows:
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
        print(f"[size_bankroll_v0] wrote {out_csv} (no slips today)")
        return

    budget, stake = float(args.budget), float(args.stake)
    sized, spend = [], 0.0
    for r in rows:
        if spend + stake > budget:
            break
        r2 = dict(r); r2["stake_total"] = f"{stake:.2f}"
        sized.append(r2); spend += stake

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sized[0].keys())
        w.writeheader(); w.writerows(sized)
    print(f"[size_bankroll_v0] wrote {out_csv} slips={len(sized)} spend=${spend:.2f} / budget=${budget:.2f}")

if __name__ == "__main__":
    main()
