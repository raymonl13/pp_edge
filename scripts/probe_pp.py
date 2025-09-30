import json, sys, urllib.request
URL = "https://api.prizepicks.com/projections?per_page=500"
headers = {
    "Origin": "https://prizepicks.com",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://prizepicks.com/"
}
req = urllib.request.Request(URL, headers=headers)
status = 0
body = b"{}"
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        status = r.getcode()
        body = r.read() or b"{}"
except Exception:
    status = 0
open("resp.json","wb").write(body)
meta = [f"HTTP_STATUS={status}"]
try:
    j = json.loads(body.decode("utf-8", "replace"))
    if isinstance(j, dict):
        items = j.get("projections",{}).get("data",[]) or j.get("data") or j.get("results") or j.get("items") or []
    elif isinstance(j, list):
        items = j
    else:
        items = []
    meta.append(f"COUNT={len(items)}")
except Exception:
    meta.append("COUNT=0")
open("probe_meta.txt","w").write("\n".join(meta)+"\n")
open("body_head.txt","w").write((body[:200]).decode("utf-8","replace").replace("\n"," ")+"\n")
