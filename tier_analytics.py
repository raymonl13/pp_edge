import typing
#!/usr/bin/env python3\nprint("Tier analytics stub")
import csv, pathlib, statistics, json, typing as _t

def _read_slips(csv_path: typing.Union[str, pathlib.Path]) -> typing.Iterator[dict]:
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            row["stake"]  = float(row["stake"])
            row["payout"] = float(row["payout"])
            yield row

def _aggregate(rows: typing.Iterable[dict]) -> list[tuple]:
    """
    Return list of tuples:
    (idx, tier, total, won, lost, stake, pnl), alphabetically by tier.
    """
    tmp: dict[str, dict[str, float]] = {}
    for r in rows:
        t = r["tier"]
        a = tmp.setdefault(t, {"total": 0, "won": 0, "lost": 0,
                               "stake": 0.0, "pnl": 0.0})
        a["total"] += 1
        a["stake"] += r["stake"]
        a["pnl"]   += r["payout"] - r["stake"]
        if r["status"] == "WON":
            a["won"] += 1
        else:
            a["lost"] += 1

    out: list[tuple] = []
    for idx, (tier, m) in enumerate(sorted(tmp.items())):
        out.append((idx, tier, m["total"], m["won"],
                    m["lost"], m["stake"], m["pnl"]))
    return out
def _write(rows: list[tuple], out_dir: pathlib.Path) -> pathlib.Path:
    import csv, datetime
    today = datetime.date.today().isoformat()
    out = out_dir / f"tier_kpi_{today}.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","tier","total","won","lost","stake","pnl"])
        for r in rows:
            w.writerow([today,*r[1:]])
    return out


# -----------------------------------------------------------------------
# CLI entry-point
# -----------------------------------------------------------------------
import os, sys, datetime, csv, pathlib, typing as _t   # re-imports safe in Py ≥3.9

def main() -> int:
    """
    Aggregate tier KPIs unless PP_EDGE_TEST_MODE is set.
    Usage: python tier_analytics.py [slip_csv]
    Returns 0 on success.
    """
    if os.getenv("PP_EDGE_TEST_MODE"):
        return 0

    slip_csv = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("data/slip_results.csv")
    rows = _aggregate(_read_slips(slip_csv))

    out_dir = pathlib.Path("analytics")
    out_dir.mkdir(parents=True, exist_ok=True)
    _write(rows, out_dir)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
