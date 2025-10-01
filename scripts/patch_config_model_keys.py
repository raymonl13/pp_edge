#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import yaml

p=Path("config_pp_edge_v6.8.yaml")
cfg={}
if p.exists():
    with p.open() as f: cfg=yaml.safe_load(f) or {}

cfg.setdefault("payouts", {"Power2":3.0,"Power3":5.0,"Power4":10.0,"Power6":25.0,"Flex4":{"4":1.5,"3":0.5},"Flex5":{"5":10.0,"4":2.0}})
cfg.setdefault("tiers", {"Demon":{"min_edge":0.12},"Goblin":{"min_edge":0.06},"Standard":{"min_edge":-1.0}})
m=cfg.setdefault("model",{})
a=m.setdefault("artifacts",{})
a.setdefault("model_path","model_assets/model_v1.pkl")
fb=m.setdefault("fallback",{})
fb.setdefault("p_hit_default",0.52)
fb.setdefault("stat_bias",{})
m.setdefault("calibration",{})

with p.open("w") as f: yaml.safe_dump(cfg,f,sort_keys=False)
print("OK")
