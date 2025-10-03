#!/usr/bin/env python3
from pathlib import Path
import sys, re

p = Path("scripts/route_fetch.py")
if not p.exists():
    print("ERROR: scripts/route_fetch.py not found"); sys.exit(1)

s = p.read_text()

old = 'datetime.utcnow().isoformat(timespec="seconds") + "Z"'
new = 'datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds").replace("+00:00","Z")'

if old in s:
    s = s.replace(old, new)
else:
    # if already patched or slightly different formatting, do a regex replacement
    s = re.sub(r'datetime\.utcnow\(\)\.isoformat\(timespec="seconds"\)\s*\+\s*"Z"',
               new, s)

# ensure ZoneInfo import exists (should already be present)
if 'from zoneinfo import ZoneInfo' not in s:
    s = s.replace('from datetime import ', 'from datetime import ')
    s = 'from zoneinfo import ZoneInfo\n' + s

p.write_text(s)
print("OK: UTC ts patch applied")
