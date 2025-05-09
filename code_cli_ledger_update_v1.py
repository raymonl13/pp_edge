"""
Nightly helper:
  • Reads data/bankroll.json
  • Updates bankroll.starting in config_pp_edge_v6.8.yaml
  • Fires milestone hooks at 5k / 10k / 25k
"""

import json, yaml, datetime, pathlib, sys

ROOT      = pathlib.Path(__file__).parent
CFG_PATH  = ROOT / "config_pp_edge_v6.8.yaml"
BANK_PATH = ROOT / "data" / "bankroll.json"
LOG_PATH  = ROOT / "data" / "logs" / "bankroll_sync.log"
MILESTONE = [5000, 10000, 25000]

def main():
    roll = json.loads(open(BANK_PATH).read())["current_bankroll"]
    cfg  = yaml.safe_load(open(CFG_PATH))
    cfg["bankroll"]["starting"] = roll
    for m in MILESTONE:
        if roll >= m and cfg["logging"].get("last_milestone", 0) < m:
            cfg["logging"]["last_milestone"] = m
            print(f"🎉  bankroll milestone reached: {m}")
    CFG_PATH.write_text(yaml.safe_dump(cfg, sort_keys=False))
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.datetime.now()} | bankroll set to {roll}\n")

if __name__ == "__main__":
    try:
        main()
        print("✅ bankroll sync complete")
    except Exception as e:
        print(f"⚠️  bankroll sync failed: {e}", file=sys.stderr)
        raise
