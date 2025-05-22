import pytest, yaml
from code_utils_bankroll_v1 import size_bet

cfg = {
    'starting': 1000,
    'kelly_fraction': 0.25,
    'max_bet_fraction_of_roll': 1,
    'daily_max_staked_pct': 1,
    'sizing': {'kelly_fraction_override': {'Demon': 0.10, 'Goblin': 0.15}}
}

def test_default_kelly():
    s = {}
    assert size_bet(0.05, cfg, s) == pytest.approx(12.5)

def test_demon_override():
    s = {}
    assert size_bet(0.05, cfg, s, tag='Demon') == pytest.approx(5.0)
