import datetime, json, os, sys, yaml, joblib, pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss
from data_utils.normalize_statcast import normalize
from code_utils_model_v1 import build_feature_df
from code_core_pp_edge_core_v6_7_v6 import run_pipeline

raw = pd.concat([
    pd.read_csv("statcast_2024.csv"),
    pd.read_csv("statcast_2025.csv")
], ignore_index=True)
df = normalize(raw)
X, y = build_feature_df(df)
probs = joblib.load("model_assets/model_v1.pkl").predict_proba(X)[:, 1]
print("AUC   :", round(roc_auc_score(y, probs), 3))
print("Brier :", round(brier_score_loss(y, probs), 3))

cfg = yaml.safe_load(open("config_pp_edge_v6.8.yaml"))
tom = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
board = f"data/pricefix_{tom}.json"
if not os.path.exists(board):
    sys.exit(f"missing board {board}")

legs = pd.read_json(board, orient="records").to_dict(orient="records")
slips = run_pipeline(legs, cfg)
pd.DataFrame(slips).to_csv(f"edge_sheet_{tom}.csv", index=False)
print(f"→ {len(legs)} legs with edge ≥ {cfg.get('min_edge_pp',0.03)}")
print(f"edge_sheet_{tom}.csv written – {len(slips)} slips generated")
