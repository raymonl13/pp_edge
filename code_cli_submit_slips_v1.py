import argparse, json, csv, sys, pathlib, uuid, datetime, yaml, requests, os
from typing import List, Dict, Any

_ROOT = pathlib.Path(__file__).resolve().parent
_CFG = yaml.safe_load((_ROOT / "config_pp_edge_v6.8.yaml").read_text())
_ENDPOINT = _CFG.get("submit", {}).get("webhook_url") or os.getenv("PP_EDGE_SANDBOX_URL", "http://localhost/mock")

def _load_payload(path: pathlib.Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))

def _dry_run(slips: List[Dict[str, Any]]) -> None:
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for s in slips:
        s.setdefault("slip_id", str(uuid.uuid4()))
        s.setdefault("submitted_at", now)
    print(json.dumps({"slips": slips, "count": len(slips)}, indent=2))

def _live_submit(slips: List[Dict[str, Any]]) -> None:
    if os.getenv("PP_EDGE_TEST_MODE"):
        _dry_run(slips)
        return
    r = requests.post(_ENDPOINT, json={"slips": slips}, timeout=10)
    if not 200 <= r.status_code < 300:
        print(f"Live submit failed [{r.status_code}] → {r.text}", file=sys.stderr)
        sys.exit(1)
    print(r.json())

def main() -> None:
    p = argparse.ArgumentParser(prog="submit_slips")
    p.add_argument("payload", type=pathlib.Path)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--live", action="store_true")
    a = p.parse_args()
    slips = _load_payload(a.payload)
    _live_submit(slips) if a.live else _dry_run(slips)

if __name__ == "__main__":
    main()
