#!/usr/bin/env python3
import json, sys, pathlib
day = sys.argv[1] if len(sys.argv) > 1 else "1970-01-01"
out = pathlib.Path(f"data/pricefix_{day}.json")
out.parent.mkdir(parents=True, exist_ok=True)
rows = [
    {"player":"Sample A","game_id":"SMK-1","p_hit":0.58,"edge_pp":0.06,"tier":"Standard","slip_type":"P4"},
    {"player":"Sample B","game_id":"SMK-2","p_hit":0.62,"edge_pp":0.08,"tier":"Standard","slip_type":"P4"}
]
with out.open("w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"Wrote {out} with {len(rows)} rows")
