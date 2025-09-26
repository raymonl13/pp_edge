
import pandas as pd
from features_travel_miles import travel_miles

def test_travel_miles_basic():
    df=pd.DataFrame({
        'team':['A','A','B'],
        'game_date':pd.to_datetime(['2024-01-01','2024-01-02','2024-01-01']),
        'park_lat':[37.7749,34.0522,40.7128],
        'park_lon':[-122.4194,-118.2437,-74.0060]
    })
    m=travel_miles(df)
    assert m.iloc[0]==0.0
    assert m.iloc[1]>0.0
    assert m.iloc[2]==0.0

