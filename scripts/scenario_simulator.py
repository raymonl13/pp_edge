import pandas as pd, argparse, pathlib, yaml

def _load_edges(path: pathlib.Path)->pd.DataFrame:
    return pd.read_csv(path)

def _load_cfg(path: pathlib.Path)->dict:
    with open(path) as f: return yaml.safe_load(f)

def simulate(edges: pd.DataFrame, unit: float)->float:
    profit=(edges['hit']*edges['payout']-unit).sum()
    return profit

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--edges',required=True)
    p.add_argument('--config',default='config_pp_edge_v6.8.yaml')
    a=p.parse_args()
    edges=_load_edges(pathlib.Path(a.edges))
    cfg=_load_cfg(pathlib.Path(a.config))
    unit=cfg['bankroll']['unit_stake']
    print({'profit':round(simulate(edges,unit),2)})
if __name__=='__main__':
    main()
