#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
p=Path("config_pp_edge_v6.8.yaml")
s=p.read_text() if p.exists() else ""
# ensure slips: block exists
if re.search(r'(?m)^\s*slips:\s*$', s) is None:
    if not s.endswith("\n"): s+="\n"
    s += "slips:\n"
# replace or insert slip_types
if re.search(r'(?m)^\s*slips:\s*(?:\n\s+.+)*\n\s*slip_types:\s*\[.*\]', s):
    s=re.sub(r'(?m)(^\s*slip_types:\s*)\[.*\]', r'\1["Power4"]', s)
elif re.search(r'(?m)^\s*slips:\s*$', s):
    s=re.sub(r'(?m)^(\s*slips:\s*$)', r'\1\n  slip_types: ["Power4"]', s)
else:
    s=re.sub(r'(?m)^(slips:\s*(?:\n\s+.+)*)$', r'\1\n  slip_types: ["Power4"]', s)
# replace or insert max_types
if re.search(r'(?m)^\s*max_types:\s*\d+', s):
    s=re.sub(r'(?m)^\s*max_types:\s*\d+', '  max_types: 1', s)
else:
    s=re.sub(r'(?m)^(\s*slips:\s*$)', r'\1\n  max_types: 1', s)
# replace or insert max_slips_per_type
if re.search(r'(?m)^\s*max_slips_per_type:\s*\d+', s):
    s=re.sub(r'(?m)^\s*max_slips_per_type:\s*\d+', '  max_slips_per_type: 3', s)
else:
    s=re.sub(r'(?m)^(\s*slips:\s*$)', r'\1\n  max_slips_per_type: 3', s)
p.write_text(s if s.endswith("\n") else s+"\n")
print("OK")
