#!/usr/bin/env python3
import argparse, os, pandas as pd, json, sys
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day", required=True)
    a=p.parse_args()
    day=a.day
    out=f"data/outcomes_{day}.csv"
    os.makedirs("data",exist_ok=True)
    r1=f"realized/realized_{day}.csv"
    if os.path.exists(out): 
        print(out); return
    if os.path.exists(r1):
        df=pd.read_csv(r1)
        if "y" not in df.columns:
            if "outcome" in df.columns: df=df.rename(columns={"outcome":"y"})
            elif "won" in df.columns: df["y"]=df["won"].astype(int)
            elif "result" in df.columns: df["y"]=df["result"].astype(int)
        cols=[c for c in ["player","stat","game_id","line","y"] if c in df.columns]
        df[cols].to_csv(out,index=False)
        print(out); return
    print("NO_OUTCOMES")
if __name__=="__main__": main()
