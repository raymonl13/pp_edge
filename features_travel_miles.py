"""Travel-Miles feature stub"""
import pandas as pd
def travel_miles(df: pd.DataFrame) -> pd.Series:
    return pd.Series(0.0, index=df.index, name="travel_miles")
