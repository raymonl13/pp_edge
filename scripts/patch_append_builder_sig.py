#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
p=Path("scripts/build_slips.py")
s=p.read_text()
if "fh.write(f\"BUILDER_SIG={BUILDER_SIG}\\n\")" not in s:
    s=s.replace('with open("run_meta.txt","a") as fh:', 'with open("run_meta.txt","a") as fh:\n        fh.write(f"BUILDER_SIG={BUILDER_SIG}\\n")')
p.write_text(s)
print("OK")
