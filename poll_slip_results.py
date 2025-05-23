import argparse, json, csv, sys, pathlib, datetime, yaml, requests, os
from typing import List, Dict, Any

_ROOT = pathlib.Path(__file__).resolve().parent
_CFG = yaml.safe_load((_ROOT / "config_pp_edge_v6.8.yaml").read_text())
_ENDPOINT = _CFG.get("submit", {}).get("result_url") or os.getenv("PP_EDGE_RESULT_URL", "http://localhost/mock_results")
_CSV_PATH = _ROOT / "data" / "slip_results.csv"
_HEADER = ["slip_id", "status", "payout", "updated_at"]

def _fetch_results() -> List[Dict[str, Any]]:
    if os.getenv("PP_EDGE_TEST_MODE"):
        return []
    r = requests.get(_ENDPOINT, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

def _append_csv(rows: List[Dict[str, Any]], csv_path: pathlib.Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    exists = csv_path.exists()
    with csv_path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_HEADER)
        if not exists:
            w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in _HEADER})

def poll(csv_path: pathlib.Path = _CSV_PATH) -> None:
    rows = _fetch_results()
    if rows:
        _append_csv(rows, csv_path)

def main() -> None:
    p = argparse.ArgumentParser(prog="poll_slip_results")
    p.add_argument("--csv", type=pathlib.Path, default=_CSV_PATH)
    a = p.parse_args()
    poll(a.csv)

if __name__ == "__main__":
    main()
