import pandas as pd, numpy as np, yaml, argparse, pathlib

def _load_edges(path: pathlib.Path)->pd.DataFrame:
    return pd.read_csv(path)

def _load_cfg(path: pathlib.Path)->dict:
    with open(path) as f: return yaml.safe_load(f)

def simulate(edges: pd.DataFrame, unit: float, runs: int, seed: int)->np.ndarray:
    rng=np.random.default_rng(seed)
    stake=np.full(len(edges),unit)
    payout=edges['payout'].values
    win_p=edges['win_prob'].values
    profit=(rng.binomial(1,win_p,(runs,len(edges)))*payout-stake).sum(axis=1)
    return profit

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--edges',required=True)
    p.add_argument('--config',default='config_pp_edge_v6.8.yaml')
    p.add_argument('--runs',type=int,default=10000)
    p.add_argument('--seed',type=int,default=42)
    a=p.parse_args()
    edges=_load_edges(pathlib.Path(a.edges))
    cfg=_load_cfg(pathlib.Path(a.config))
    unit=cfg['bankroll']['unit_stake']
    bankroll=cfg['bankroll']['starting_bankroll']
    results=bankroll+simulate(edges,unit,a.runs,a.seed)
    q=np.percentile(results,[5,50,95]).round(2)
    print({'p5':q[0],'p50':q[1],'p95':q[2]})
if __name__=='__main__':
    main()
