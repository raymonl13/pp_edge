import json, sys, argparse, datetime, http.client, urllib.parse
def _post(url:str,payload:dict)->int:
    u=urllib.parse.urlparse(url)
    Conn=http.client.HTTPSConnection if u.scheme=="https" else http.client.HTTPConnection
    c=Conn(u.netloc,timeout=10)
    c.request("POST",u.path or "/",body=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    return c.getresponse().status
def main():
    p=argparse.ArgumentParser(prog="notify")
    p.add_argument("kind",choices=["nightly","var"]);p.add_argument("--url",required=True);p.add_argument("--value",type=float,default=0.0)
    a=p.parse_args()
    txt="✅ Nightly cron finished" if a.kind=="nightly" else f"⚠️ VaR breach: ${a.value:,.2f}"
    sys.exit(0 if 200<=_post(a.url,{"text":txt})<300 else 1)
if __name__=="__main__":main()
