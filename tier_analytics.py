import argparse, csv, pathlib, datetime, statistics, os
from typing import List, Dict

_ROOT = pathlib.Path(__file__).resolve().parent
_SLIP_CSV = _ROOT / "data" / "slip_results.csv"
_OUT_DIR = _ROOT / "analytics"
_HEADERS = ["date", "tier", "total", "wins", "losses", "win_rate", "pnl", "var_95"]

def _read_slips(path: pathlib.Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))

def _calc_pnl(row: Dict[str, str]) -> float:
    status = row.get("status", "").upper()
    stake = float(row.get("stake", 0))
    payout = float(row.get("payout", 0))
    return payout - stake if status == "WON" else -stake if status == "LOST" else 0.0

def _aggregate(rows: List[Dict[str, str]]) -> List[List]:
    tiers = {}
    for r in rows:
        t = r.get("tier", "UNKNOWN")
        tiers.setdefault(t, []).append(r)
    out = []
    today = datetime.date.today().isoformat()
    for tier, rs in tiers.items():
        total = len(rs)
        wins = sum(1 for r in rs if r.get("status", "").upper() == "WON")
        losses = sum(1 for r in rs if r.get("status", "").upper() == "LOST")
        pnl_list = [_calc_pnl(r) for r in rs]
        pnl = round(sum(pnl_list), 2)
        win_rate = round(wins / total, 3) if total else 0
        var_95 = round(statistics.quantiles(pnl_list, n=20)[0], 2) if total >= 20 else 0
        out.append([today, tier, total, wins, losses, win_rate, pnl, var_95])
    return out

def _write(out_rows: List[List], out_dir: pathlib.Path) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"tier_kpi_{datetime.date.today().isoformat()}.csv"
    fpath = out_dir / fname
    with fpath.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(_HEADERS)
        w.writerows(out_rows)
    return fpath

def main() -> None:
    p = argparse.ArgumentParser(prog="tier_analytics")
    p.add_argument("--slips", type=pathlib.Path, default=_SLIP_CSV)
    p.add_argument("--outdir", type=pathlib.Path, default=_OUT_DIR)
    a = p.parse_args()
    if os.getenv("PP_EDGE_TEST_MODE"):
        return
    rows = _read_slips(a.slips)
    out = _aggregate(rows)
    if out:
        _write(out, a.outdir)

if __name__ == "__main__":
    main()
