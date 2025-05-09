
import pandas as pd
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv = ROOT / 'metrics' / 'hit_prob.csv'
csv.parent.mkdir(exist_ok=True)
if not csv.exists():
    csv.write_text('run_date,roc_auc,calibration_slope\n')
today = date.today().isoformat()
csv.write_text(csv.read_text() + f'{today},0.0,0.0\n')
print('Nightly placeholder metrics appended')
