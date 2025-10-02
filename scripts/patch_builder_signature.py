#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path,re
p=Path("scripts/build_slips.py")
s=p.read_text()
if "BUILDER_SIG=" not in s:
    s=s.replace("def main():", 'BUILDER_SIG="v6.0-feas-fallback-players-only"\n\ndef main():')
p.write_text(s)
print("OK")
