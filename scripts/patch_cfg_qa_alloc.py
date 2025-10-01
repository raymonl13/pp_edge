#!/usr/bin/env python3
from pathlib import Path
def main():
    cfg_path=Path("config_pp_edge_v6.8.yaml")
    if not cfg_path.exists(): raise SystemExit("config_pp_edge_v6.8.yaml not found")
    import yaml
    cfg=yaml.safe_load(cfg_path.read_text()) or {}
    desired={"qa":{"min_rows":100,"max_demon_per_slip":1},"allocator":{"starting":1000.0,"slip_cap":25.0,"slate_cap_frac":0.1,"kelly_fraction":0.5},"tiers":{"kelly_multiplier":{"Demon":1.2,"Goblin":0.9,"Standard":1.0}}}
    for k,v in desired.items():
        if isinstance(v,dict) and isinstance(cfg.get(k),dict): cfg[k].update(v)
        else: cfg[k]=v
    cfg_path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    print("OK")
if __name__=="__main__": main()
