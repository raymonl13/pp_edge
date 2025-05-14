import yaml, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
_FIX = yaml.safe_load((ROOT / "fixtures.yaml").read_text())
def get_fixture(name: str):
    return ROOT / _FIX[name]
