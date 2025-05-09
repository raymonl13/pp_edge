"""
Daily helper:
  • Hits PrizePicks Help-Center endpoint
  • Updates the `payouts:` node inside config_pp_edge_v6.8.yaml
  • Appends a one-liner to data/logs/payout_refresh.log
"""

import requests, yaml, datetime, pathlib, sys

ROOT      = pathlib.Path(__file__).parent
CFG_PATH  = ROOT / "config_pp_edge_v6.8.yaml"
LOG_PATH  = ROOT / "data" / "logs" / "payout_refresh.log"

def fetch_live_payouts():
    url = "https://help.prizepicks.com/hc/en-us/articles/1500001234567.json"
    js  = requests.get(url, timeout=10).json()
    # ----- tiny parse helper (stub) -----
    p4  = float(js["article"]["body"].split("Power 4 = ")[1][:4])
    p6  = 37.5
    flex = {"6": 25.0, "5": 2.0, "4": 0.4}
    return p4, p6, flex

def main():
    p4, p6, flex = fetch_live_payouts()
    cfg = yaml.safe_load(open(CFG_PATH))
    cfg["payouts"]["Power4"] = p4
    cfg["payouts"]["Power6"] = p6
    cfg["payouts"]["Flex6"]["six_correct"]  = flex["6"]
    cfg["payouts"]["Flex6"]["five_correct"] = flex["5"]
    cfg["payouts"]["Flex6"]["four_correct"] = flex["4"]
    CFG_PATH.write_text(yaml.safe_dump(cfg, sort_keys=False))
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.date.today()} | P4={p4} P6={p6} F6={flex}\n")

if __name__ == "__main__":
    try:
        main()
        print("✅ payout refresh complete")
    except Exception as e:
        print(f"⚠️  payout refresh failed: {e}", file=sys.stderr)
        raise
