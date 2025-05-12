import importlib, json, yaml, pathlib
core = importlib.import_module("code_core_pp_edge_core_v6_7_v6")
ROOT = pathlib.Path(__file__).resolve().parent
cfg  = yaml.safe_load((ROOT / "config_pp_edge_v6.8.yaml").read_text())
legs = json.loads((ROOT / "demo_slipbuilder_input.json").read_text())["legs"]
def test_demo_slipbuilder():
    assert core.run_pipeline(legs, cfg)
