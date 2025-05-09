"""
Quick smoke-test for SlipBuilder + Core v4
Prints the first two slips.
"""
import json, yaml, pathlib, pprint, sys

ROOT = pathlib.Path(__file__).parent
sys.path.append(str(ROOT))                 # ensure imports work

from code_core_pp_edge_core_v6_7_v4 import run_pipeline

cfg_path  = ROOT / "config_pp_edge_v6.8.yaml"
feed_path = ROOT / "data_feed_sample.json"   # adjust if yours lives elsewhere

with cfg_path.open() as f:
    cfg = yaml.safe_load(f)
with feed_path.open() as f:
    raw = json.load(f)["projections"]

pprint.pp(run_pipeline(raw, cfg)[:2])
print("\n✅  Smoke-test complete.")
