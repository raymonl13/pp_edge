import pandas as pd
from data_utils.load_park_factors import get_park_factors

COLUMN_MAP = {
    "home_team": "team_id",
    "batter"   : "batter_id",
    "barrel"   : "barrel",
}
REQ = ["game_date","team_id","batter_id","pitcher"]

def _derive_barrel_bool(df: pd.DataFrame) -> pd.Series:
    speed = pd.to_numeric(df["launch_speed"], errors="coerce")
    angle = pd.to_numeric(df["launch_angle"], errors="coerce")
    return ((speed>98)&(angle.between(26,30))).astype(float)

def _derive_pitcher_swstr(df: pd.DataFrame) -> pd.Series:
    whiff = df["description"].str.contains("swinging_strike", na=False)
    return whiff.groupby(df["pitcher"]).transform("mean").fillna(0.0)

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=COLUMN_MAP, errors="ignore")
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values("game_date").reset_index(drop=True)


    if "barrel" not in df or df["barrel"].nunique() <= 1:
        df["barrel"] = _derive_barrel_bool(df)
    if "pitcher_swstr" not in df:
        df["pitcher_swstr"] = _derive_pitcher_swstr(df)


    df = df.merge(get_park_factors(), on="team_id", how="left")

    miss=[c for c in REQ if c not in df.columns]
    if miss: raise KeyError(f"normalize missing {miss}")
    return df
