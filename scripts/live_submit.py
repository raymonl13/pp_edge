import json, os, sys, requests

def main():
    mode = os.getenv("PPEDGE_MODE", "test")
    with open(sys.argv[1]) as f:
        payload = json.load(f)
    if mode != "live":
        print(json.dumps(payload))
        return 0
    url = os.getenv("PPEDGE_SUBMIT_URL")
    token = os.getenv("PPEDGE_LIVE_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    print(resp.text)
    return 0

if __name__ == "__main__":
    sys.exit(main())
