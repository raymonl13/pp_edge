#!/usr/bin/env python3
import os, json, pathlib
pathlib.Path("outcomes").mkdir(parents=True, exist_ok=True)
p = pathlib.Path("outcomes/outcomes_summary.json")
if not p.exists() or p.stat().st_size == 0:
    day = os.environ.get("DAY","")
    json.dump({"status":"PENDING","day":day,"notes":"skeleton"}, p.open("w"))
print(str(p))
