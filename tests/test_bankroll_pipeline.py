
import json, yaml, pathlib
from code_core_pp_edge_core_v6_7_v6 import run_pipeline

ROOT = pathlib.Path(__file__).resolve().parents[1]
cfg  = yaml.safe_load((ROOT/'config_pp_edge_v6.8.yaml').read_text())

def _legs(name):
    return json.loads((ROOT/'tests'/name).read_text())['legs']

def test_multi_game_slips():
    assert len(run_pipeline(_legs('multi_game.json'), cfg)) >= 1

def test_single_game_zero_slips():
    assert len(run_pipeline(_legs('single_game.json'), cfg)) == 0
