#!/usr/bin/env python3
import argparse, datetime, sys, os
def parse_iso(s): return datetime.date.fromisoformat(s)
def day_iso(d): return d.isoformat()
def compute_range(start, end):
    step=datetime.timedelta(days=1); d=start
    while d<=end:
        yield d
        d+=step
def normalize_args(args):
    today=parse_iso(args.today) if args.today else datetime.date.today()
    end=parse_iso(args.end) if args.end else today-datetime.timedelta(days=1)
    look=int(args.days) if args.days is not None else 14
    start=parse_iso(args.start) if args.start else end-datetime.timedelta(days=look-1)
    if start>end:
        start,end=end,start
    return start,end
def main():
    p=argparse.ArgumentParser(description="Emit inclusive ISO date range")
    p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--days",type=int); p.add_argument("--today"); p.add_argument("--out",default="outcomes_dates.txt")
    args=p.parse_args(); start,end=normalize_args(args)
    dates=[day_iso(d) for d in compute_range(start,end)]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out,"w") as fh:
        for d in dates: fh.write(d+"\n")
    for d in dates: print(d)
    print(f"outcomes_backfill_range start={dates[0]} end={dates[-1]} n_days={len(dates)}", file=sys.stderr)
if __name__=="__main__": main()
