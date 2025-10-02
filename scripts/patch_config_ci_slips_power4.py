#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import yaml
p=Path("config_pp_edge_v6.8.yaml")
cfg=yaml.safe_load(p.read_text()) if p.exists() else {}
sl=cfg.setdefault("slips",{})
sl["slip_types"]=["Power4"]
sl["max_types"]=1
sl["max_slips_per_type"]=3
p.write_text(yaml.safe_dump(cfg, sort_keys=False))
print("OK")
