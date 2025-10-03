#!/usr/bin/env python3
import sys, json
from pathlib import Path

def find_first(root: Path, name: str) -> Path | None:
    for p in root.rglob(name):
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    dbg = find_first(root, "route_debug.json")
    if not dbg:
        print("ROUTER_ASSERT: route_debug.json missing"); sys.exit(2)
    d = json.loads(dbg.read_text())
    src = d.get("source"); state = d.get("ROUTE_STATE")
    http = d.get("HTTP_STATUS"); rows = int(d.get("row_count", 0))
    sha = d.get("board_sha16"); noop = bool(d.get("ROUTE_NOOP"))
    print(f"ROUTER_ASSERT: source={src} state={state} http={http} rows={rows} sha16={sha} noop={noop}")
    if src == "http" and rows == 0 and not noop:
        print("ROUTER_ASSERT: http chosen but produced 0 rows and did not retain prior board"); sys.exit(3)
    print("ROUTER_ASSERT: PASS"); sys.exit(0)

if __name__ == "__main__":
    main()
