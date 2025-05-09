
import importlib, yaml
def test_pipeline_runs():
    core = importlib.import_module('code_core_pp_edge_core_v6_7_v6')
    cfg = yaml.safe_load(open('config_pp_edge_v6.8.yaml'))
    legs = [
        {'player': 'Unit Tester', 'team': 'NYY', 'stat': 'Hits'},
        {'player': 'Unit Tester 2', 'team': 'LAD', 'stat': 'HR'}
    ]
    df = core.run_pipeline(legs, cfg)
    if isinstance(df, list):
        assert all('p_hit' in leg for leg in df)
    else:
        assert 'p_hit' in df.columns
