import pandas as pd
from scripts.monte_carlo_bankroll import simulate

def test_simulate_basic():
    df=pd.DataFrame({'win_prob':[0.55,0.45],'payout':[1.9,1.8]})
    res=simulate(df,1,5000,0)
    assert res.mean()>-1 and res.mean()<1
