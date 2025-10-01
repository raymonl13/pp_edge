#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

p=Path("config_pp_edge_v6.8.yaml")
s=p.read_text() if p.exists() else ""
if "payouts:" not in s:
    s += ("\npayouts:\n"
          "  Power2: 3.0\n  Power3: 5.0\n  Power4: 10.0\n  Power6: 25.0\n"
          "  Flex4:\n    \"4\": 1.5\n    \"3\": 0.5\n"
          "  Flex5:\n    \"5\": 10.0\n    \"4\": 2.0\n")
if "tiers:" not in s:
    s += ("\ntiers:\n"
          "  Demon:\n    min_edge: 0.12\n"
          "  Goblin:\n    min_edge: 0.06\n"
          "  Standard:\n    min_edge: -1.0\n")
if "model:" not in s:
    s += ("\nmodel:\n"
          "  artifacts:\n    model_path: model_assets/model_v1.pkl\n"
          "  fallback:\n    p_hit_default: 0.52\n    stat_bias: {}\n"
          "  calibration: {}\n")
p.write_text(s if s.endswith("\n") else s+"\n")
print("OK")
