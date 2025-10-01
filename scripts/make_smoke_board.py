#!/usr/bin/env python3
from __future__ import annotations
import json, datetime
from pathlib import Path
day = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
Path("data").mkdir(exist_ok=True)
rows = [
    {"player":"Test A","team":"SMK","stat":"PTS","line":22.5},
    {"player":"Test B","team":"SMK","stat":"REB","line":7.5},
]
Path(f"data/pricefix_{day}.json").write_text(json.dumps(rows))
print(f"Wrote data/pricefix_{day}.json with {len(rows)} rows")
