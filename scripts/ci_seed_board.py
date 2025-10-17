#!/usr/bin/env python3
import argparse, datetime as dt, json, os, pandas as pd
def make_board(day):
    return [
        {"player":"Julio Rodríguez","team":"SEA","stat":"PTS","line":None},
        {"player":"Daulton Varsho","team":"TOR","stat":"PTS","line":None},
        {"player":"Anthony Santander","team":"TOR","stat":"PTS","line":None},
        {"player":"Max Muncy","team":"LAD","stat":"PTS","line":None}
    ]
def make_edges(day):
    legs=[
        {"player":"Julio Rodríguez","team":"SEA","stat":"PTS","line":None,"prob":0.5,"p_hit":0.5,"edge_pp":4.0,"tier":"goblin"},
        {"player":"Daulton Varsho","team":"TOR","stat":"PTS","line":None,"prob":0.5,"p_hit":0.5,"edge_pp":4.0,"tier":"goblin"},
        {"player":"Anthony Santander","team":"TOR","stat":"PTS","line":None,"prob":0.5,"p_hit":0.5,"edge_pp":4.0,"tier":"goblin"},
        {"player":"Max Muncy","team":"LAD","stat":"PTS","line":None,"prob":0.5,"p_hit":0.5,"edge_pp":4.0,"tier":"goblin"}
    ]
    row={"slip_type":"Power4","legs":str(legs),"edge_pp":-0.375,"stake_total":""}
    return pd.DataFrame([row])
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day")
    p.add_argument("--out-board",required=True)
    p.add_argument("--out-edges",required=True)
    a=p.parse_args()
    day=a.day or dt.date.today().isoformat()
    os.makedirs(os.path.dirname(a.out_board) or ".", exist_ok=True)
    with open(a.out_board,"w") as f: json.dump(make_board(day),f)
    make_edges(day).to_csv(a.out_edges,index=False)
    print(a.out_board); print(a.out_edges)
if __name__=="__main__": main()
