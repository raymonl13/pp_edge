
import pandas as pd, numpy as np

def _haversine(lat1, lon1, lat2, lon2):
    r=3958.8
    lat1=np.radians(lat1); lat2=np.radians(lat2)
    dlat=lat2-lat1
    dlon=np.radians(lon2-lon1)
    a=np.sin(dlat/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return r*2*np.arcsin(np.sqrt(a))

def travel_miles(df:pd.DataFrame)->pd.Series:
    d=df[['team','game_date','park_lat','park_lon']].copy()
    d.sort_values(['team','game_date'],inplace=True)
    d['prev_lat']=d.groupby('team')['park_lat'].shift()
    d['prev_lon']=d.groupby('team')['park_lon'].shift()
    miles=_haversine(d['prev_lat'],d['prev_lon'],d['park_lat'],d['park_lon']).fillna(0.0)
    return miles.reindex(df.index).astype(float).rename('travel_miles')

