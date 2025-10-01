#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
p=Path("scripts/score_board.py"); s=p.read_text()
s=re.sub(r"return min\(edge, 0\.18\)", "return min(edge, 0.12)", s)
s=re.sub(r"slip_types = \[k for k in slip_types if k in \(\"Power2\",\"Power3\"\)\]", "slip_types = [k for k in slip_types if k in (\"Power2\",)]", s)
p.write_text(s)
print("OK")
