#!/usr/bin/env python3
import argparse,glob,json,math,os
import numpy as np,pandas as pd
def load_joined(outdir):
    paths=sorted(glob.glob(f"{outdir}/day=*/joined.csv"))
    frames=[]
    for p in paths:
        try:
            df=pd.read_csv(p,usecols=["p_raw","y"])
            frames.append(df)
        except Exception:
            continue
    if not frames: return pd.DataFrame(columns=["p_raw","y"])
    return pd.concat(frames,ignore_index=True)
def clip01(x,eps=1e-6): return np.clip(x,eps,1-eps)
def fit_platt(p,y,maxit=50,tol=1e-6):
    p=clip01(p); y=y.astype(float)
    z=np.log(p/(1-p)); a=1.0; b=0.0
    for _ in range(maxit):
        t=a*z+b; q=1.0/(1.0+np.exp(-t))
        w=q*(1-q); s=y-q
        g1=np.sum(w*z*z); g2=np.sum(w*z); g3=np.sum(w)
        h1=np.sum(s*z); h2=np.sum(s)
        det=g1*g3-g2*g2
        if abs(det)<1e-12: break
        da=(h1*g3-h2*g2)/det; db=(g1*h2-g2*h1)/det
        a+=da; b+=db
        if max(abs(da),abs(db))<tol: break
    return float(a),float(b)
def pav_isotonic(x,y,w=None):
    if w is None: w=np.ones_like(y)
    order=np.argsort(x)
    x,y,w=x[order],y[order],w[order]
    yhat=y.copy(); blocks=[[i] for i in range(len(y))]
    def avg(idxs): 
        ww=w[idxs]; vv=y[idxs]; 
        return np.sum(ww*vv)/np.sum(ww)
    i=0
    while i<len(blocks)-1:
        a=avg(blocks[i]); b=avg(blocks[i+1])
        if a<=b: i+=1
        else:
            blocks[i]+=blocks[i+1]; del blocks[i+1]
            while i>0:
                a=avg(blocks[i-1]); b=avg(blocks[i])
                if a<=b: break
                blocks[i-1]+=blocks[i]; del blocks[i]
                i-=1
    for blk in blocks:
        m=avg(blk)
        for j in blk: yhat[j]=m
    out=np.empty_like(yhat)
    out[order]=yhat
    return out
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",default="outcomes")
    ap.add_argument("--artifact",default="calibration")
    ap.add_argument("--method",choices=["auto","platt","isotonic"],default="auto")
    ap.add_argument("--min_samples",type=int,default=20)
    args=ap.parse_args()
    os.makedirs(args.artifact,exist_ok=True)
    df=load_joined(args.outdir)
    df=df.dropna(subset=["p_raw","y"])
    n=len(df)
    if n<args.min_samples:
        meta={"status":"insufficient","n":int(n)}
        json.dump(meta,open(f"{args.artifact}/latest.json","w"))
        print(json.dumps(meta))
        return
    p=df["p_raw"].to_numpy(dtype=float)
    y=df["y"].to_numpy(dtype=float)
    if args.method=="auto":
        try:
            a,b=fit_platt(p,y)
            meth="platt"; payload={"method":"platt","a":a,"b":b,"n":int(n)}
        except Exception:
            yh=pav_isotonic(p,y)
            pairs=[[float(pi),float(yi)] for pi,yi in zip(np.linspace(0,1,11),np.interp(np.linspace(0,1,11),np.sort(p),np.sort(y)))]
            meth="isotonic"; payload={"method":"isotonic","pairs":pairs,"n":int(n)}
    elif args.method=="platt":
        a,b=fit_platt(p,y); meth="platt"; payload={"method":"platt","a":a,"b":b,"n":int(n)}
    else:
        yh=pav_isotonic(p,y)
        pairs=[[float(pi),float(yi)] for pi,yi in zip(np.linspace(0,1,11),np.interp(np.linspace(0,1,11),np.sort(p),np.sort(y)))]
        meth="isotonic"; payload={"method":"isotonic","pairs":pairs,"n":int(n)}
    json.dump(payload,open(f"{args.artifact}/latest.json","w"))
    print(json.dumps({"status":"ok","method":meth,"n":int(n)}))
if __name__=="__main__":
    main()
