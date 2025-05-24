import argparse, sys, datetime as dt, pandas as pd, logging
from pathlib import Path
from typing import Tuple
from importlib import import_module
from tenacity import retry, stop_after_attempt, wait_exponential
from pybaseball import statcast, cache
cache.enable()
try:
    pb_utils = import_module("pybaseball.utils")
    if hasattr(pb_utils, "session"):
        pb_utils.session.headers.update({"User-Agent": "pp-edge-bot/2.0"})
except Exception:
    pass
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
def season_window(season:int)->Tuple[str,str]:
    start=f"{season}-01-01"
    today=dt.date.today()
    end=today.strftime("%Y-%m-%d") if today.year==season else f"{season}-12-31"
    return start,end
def days_window(days:int)->Tuple[str,str]:
    end=dt.date.today()
    start=end-dt.timedelta(days=days)
    return start.strftime("%Y-%m-%d"),end.strftime("%Y-%m-%d")
@retry(stop=stop_after_attempt(5),wait=wait_exponential(multiplier=1,max=60))
def fetch_statcast(start:str,end:str)->pd.DataFrame:
    logging.info("%s → %s",start,end)
    return statcast(start_dt=start,end_dt=end)
def to_csv(df:pd.DataFrame,start:str,end:str)->Path:
    fname=f"statcast_{start}_{end}.csv".replace("-","")
    out_path=RAW_DIR/fname
    df.to_csv(out_path,index=False)
    logging.info("Saved %d rows to %s",len(df),out_path)
    return out_path
def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--season",type=int)
    parser.add_argument("--days",type=int)
    args=parser.parse_args(argv)
    if args.days:
        start,end=days_window(args.days)
    else:
        season=args.season or dt.date.today().year
        start,end=season_window(season)
    df=fetch_statcast(start,end)
    to_csv(df,start,end)
if __name__=="__main__":
    sys.exit(main())
