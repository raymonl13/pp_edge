import pandas as pd, pytest
from scripts.scenario_simulator import simulate

def test_simulate_scenario():
    df=pd.DataFrame({'hit':[1,0,1],'payout':[1.9,2.0,1.8]})
    assert simulate(df,1) == pytest.approx(0.7)
