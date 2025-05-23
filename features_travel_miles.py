import pandas as pd, numpy as np
from math import radians, sin, cos, sqrt, atan2
_R=3958.8
def _h(lat1,lon1,lat2,lon2):
    dlat=radians(lat2-lat1);dlon=radians(lon2-lon1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*_R*atan2(sqrt(a),sqrt(1-a))
def travel_miles(df:pd.DataFrame)->pd.Series:
    df=df.sort_values(["team","game_date"]).reset_index(drop=True)
    miles=np.zeros(len(df))
    for team,g in df.groupby("team"):
        lat,lon=g["park_lat"].values,g["park_lon"].values
        idx=g.index
        seg=[_h(lat[i-1],lon[i-1],lat[i],lon[i]) for i in range(1,len(lat))]
        miles[idx[1:]]=seg
    return pd.Series(miles,index=df.index)
