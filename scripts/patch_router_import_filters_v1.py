#!/usr/bin/env python3
from pathlib import Path
import sys, re

def patch_file(p: Path):
    if not p.exists():
        print(f"SKIP: {p} not found"); return False
    s = p.read_text()

    # If filters already present, no-op
    if "warnings.filterwarnings(" in s and "module=\"requests\"" in s:
        return False

    # Insert filters before the first occurrence of "import requests"
    if "import requests" not in s:
        print(f"NOTE: {p} has no 'import requests'; skipping") 
        return False

    # Ensure 'import warnings' exists above requests import
    lines = s.splitlines()
    out = []
    inserted_filters = False
    for i, line in enumerate(lines):
        if not inserted_filters and re.match(r'^\s*import\s+requests\b', line):
            out.append("import warnings")
            out.append('warnings.filterwarnings("ignore", module="requests")')
            out.append('warnings.filterwarnings("ignore", module="urllib3")')
            out.append('warnings.filterwarnings("ignore", module="idna")')
            out.append('warnings.filterwarnings("ignore", module="charset_normalizer")')
            out.append('warnings.filterwarnings("ignore", module="yaml")')
            inserted_filters = True
        out.append(line)

    new = "\n".join(out) + ("\n" if not out[-1].endswith("\n") else "")
    if new != s:
        p.write_text(new)
        return True
    return False

changed = False
for rel in ("scripts/route_fetch.py", "scripts/route_smoke.py"):
    if patch_file(Path(rel)):
        print(f"OK: inserted warning filters in {rel}")
        changed = True

if not changed:
    print("NOTE: no changes needed")
