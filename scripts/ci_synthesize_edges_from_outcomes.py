#!/usr/bin/env python3
import os,csv,argparse,pandas as pd
def synth(day,limit):
    src=f"data/outcomes_{day}.csv"
    if not os.path.exists(src): return "no_outcomes"
    df=pd.read_csv(src)
    if df.empty: return "no_rows"
    cols={c.lower():c for c in df.columns}
    def pick(*ks):
        for k in ks:
            if k in cols: return cols[k]
        return None
    pcol=pick("p_raw","prob","p_hit")
    lcol=pick("line_real","line")
    scol=pick("stat")
    plcol=pick("player","name","player_name","athlete","full_name")
    if plcol is None: return "no_player_col"
    out=f"edge_sheet_{day}.csv"
    with open(out,"w",newline="") as fh:
        fn=["player","stat","line","p_hit","payout","tier","game_id"]
        w=csv.DictWriter(fh,fieldnames=fn); w.writeheader()
        n=0; N=min(limit,len(df))
        for _,r in df.iterrows():
            if n>=N: break
            player=str(r[plcol]).strip()
            stat=str(r[scol]).strip() if scol else "PTS"
            try: line=float(r[lcol]) if lcol and pd.notna(r[lcol]) else ""
            except: line=""
            pr=None
            if pcol is not None:
                try: pr=float(r[pcol])
                except: pr=None
            if pr is None or not (0.0<=pr<=1.0):
                base=0.1+0.8*(n/max(1,N-1))
                pr=max(0.05,min(0.95,base))
            w.writerow({"player":player,"stat":stat,"line":line,"p_hit":pr,"payout":2.0,"tier":"synth","game_id":""})
            n+=1
    return out
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--day",required=True)
    ap.add_argument("--max",type=int,default=12)
    a=ap.parse_args()
    print(synth(a.day,a.max))
if __name__=="__main__":
    main()
