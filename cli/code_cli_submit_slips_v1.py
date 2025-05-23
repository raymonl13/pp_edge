import argparse, json, csv, sys, pathlib, uuid, datetime
from typing import List, Dict, Any

def _load_payload(path: pathlib.Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())
    rows = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows

def _dry_run(slips: List[Dict[str, Any]]) -> None:
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for s in slips:
        s.setdefault("slip_id", str(uuid.uuid4()))
        s.setdefault("submitted_at", now)
    print(json.dumps({"slips": slips, "count": len(slips)}, indent=2))

def main() -> None:
    p = argparse.ArgumentParser(prog="submit_slips", description="Dry-run PrizePicks submission CLI")
    p.add_argument("payload", type=pathlib.Path, help="JSON or CSV file with slips")
    p.add_argument("--dry-run", action="store_true", default=False, help="Print payload instead of POST")
    args = p.parse_args()
    slips = _load_payload(args.payload)
    if args.dry_run:
        _dry_run(slips)
        sys.exit(0)
    print("Live submit not implemented; use --dry-run", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
