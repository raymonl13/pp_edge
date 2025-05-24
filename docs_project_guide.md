# PP-EDGE Project Guide  (v1.1 - 06-May-2025)

This file is the canonical reference for every ChatGPT conversation in the "PP-EDGE v6.7 Build-Out" project.
Keep it updated; pin the Dashboard chat in your sidebar.

---

## 1 Drive / Colab folder map

/content/drive/My Drive/pp_edge/    <-- ROOT  
- code_core_pp_edge_core_v6_7_v#.py  
- code_cli_pp_edge_engine_v#.py  
- code_cli_pp_edge_scraper_v#.py  
- code_utils_*_v#.py  
- config_pp_edge_v6.#.yaml  
- data/  
    - live_feeds_YYYY-MM-DD.json  
    - data_feed_sample.json  
    - bankroll.json  
    - logs/  
- docs_project_guide.md  

---

## 2 Naming-prefix convention

Prefix       | Meaning                         | Example
------------ | ------------------------------- | ----------------------------
code_core_   | Engine modules                  | code_core_pp_edge_core_v6_7_v2.py  
code_cli_    | Stand-alone wrappers            | code_cli_pp_edge_engine_v1.py  
code_utils_  | Helper libs (bankroll, VaR…)     | code_utils_bankroll_v1.py  
config_      | YAML configs                    | config_pp_edge_v6.8.yaml  
data_        | Sample or synthetic data        | data_feed_sample.json  
(none)       | Large feeds in /data            | data/live_feeds_2025-05-06.json  
docs_        | Markdown docs                   | docs_project_guide.md  

---

## 3 Milestone flow

ID | Chat title (pinned)     | Deliverable  
---|-------------------------|--------------------------------  
M0 | PP-EDGE Dashboard       | Status table & parking-lot ideas  
M1 | Parser Build            | _simplify_props() done  
M2 | Bayesian Hit-Prob       | bayes_hit_prob() + priors validated  
M3 | Edge & Payout Logic     | calc_edge() + payouts synced  
M4 | Diversification & Quotas| build_slips() respects YAML caps  
M5 | Kelly Bankroll          | code_utils_bankroll_v1.py + YAML hooks  
M6 | Monte-Carlo VaR         | code_utils_mc_var_v1.py wired in  
M7 | Renderer Polish         | Pretty JSON/Markdown output  
M8 | Daily Runner Notebook   | notebook_pp_edge_daily_runner.ipynb  

---

## 4 Colab quick-start snippet

```python
from google.colab import drive
drive.mount('/content/drive')
ROOT = "/content/drive/My Drive/pp_edge"

!pip install -q pyyaml requests

%run $ROOT/code_utils/fetch_payouts.py
%run $ROOT/code_utils/ledger_update.py

!python $ROOT/code_cli_pp_edge_engine_v1.py \
  --yaml $ROOT/config_pp_edge_v6.8.yaml \
  --date $(date -I) \
  --feeds $ROOT/data/live_feeds_$(date -I).json

  5 Math Reference – Leg-level Edge
ini
Copy
Edit
EV_leg   = p_hit * payout - 1
edge_pct = EV_leg
6 Data & Logging – per-leg record
Field	Notes
run_id	ISO timestamp
leg_id	UUID
player	Player name
stat	e.g. "HR", "PTS"
line	Site line
projection	Model mean (optional)
p_hit	Win probability 0–1
payout	From leg_payouts
ev_units	p_hit * payout - 1
edge_pct	ev_units * 100
kelly_fraction_full	Raw full-Kelly
kelly_fraction_used	After safety dials
stake_units	Dollars/units risked
bankroll_before	Balance before stake
status	pending → won/lost

6 Code-cell Convention
# — no inline comments —
<clean command 1>
<clean command 2>
<clean command 3>
(Closing heredocs or JSON blocks follow the same minimal style.)

Context checklist (always immediately below the code block)
Step 1 Describe what <clean command 1> does.

Step 2 Describe what <clean command 2> does.

Step 3 Describe what <clean command 3> does.



## GitHub as Single Source of Truth
- **Start each session or Colab notebook** with Already up to date. to sync the latest code.
- **After pushing changes**, run  in Colab to fetch updates before running any cells.

### CI Fixture Rules
* All sample data lives under `data/raw/` and is **un-ignored** in `.gitignore`.
* Every CSV must carry columns required by current feature functions.
* The workflow’s “fixture-smoke” step fails if a required column disappears.

### Monte-Carlo & Tier Sizing (added in v6.7.1)
* `scripts/monte_carlo_bankroll.py` simulates 10 000 slates and outputs VaR / P-land.
* Demon stake floor and Goblin cap are read from `config_pp_edge_v6.8.yaml`.

### Nightly Edge-Sheet Cron
* `.github/workflows/nightly_edge_sheet.yml` runs at **08:00 UTC**.
* It executes `run_edge_sheet.py`, uploads `edge_sheet_<date>.csv` as a workflow artifact, and posts summary metrics to Slack (Webhook ID in repo secret).

### Live Submission Flow (added in v8.0)
* `code_cli_submit_slips_v1.py` builds JSON/CSV payloads.
* `--dry-run` prints payload; `--live` (Phase 5) will POST to PrizePicks sandbox.
* Reads `submit:` block in `config_pp_edge_v6.8.yaml` for `mode` and `webhook_url`.

### Result Poller
* `poll_slip_results.py` polls the sandbox API every 30 s.
* Writes status updates to `data/slip_results.csv` for dashboard ingestion.

### Tier Analytics
* `tier_analytics.py` aggregates Demon/Goblin win-rate, P/L, and VaR trend.
* Outputs `analytics/tier_kpi_<date>.csv`; dashboard v3 visualises the KPIs.

### Stub-Audit & Coverage Badge
* `.github/workflows/stub_audit.yml` fails CI if any `TODO STUB` remains in repo.
* CI uses `pytest-cov`; build fails if coverage \< 80 %.  
  Badge is displayed in the project README.

### Model Retraining & Calibration (v9.0)
* `code_data_ingest_statcast_v2.py` ingests 2026 YTD Statcast & merges park factors.
* `train_hit_prob_v2.py` trains LightGBM and saves `model_assets/model_v2.pkl`.
* `calibrate_hit_prob.py` fits isotonic (or Platt) scaling; params stored in YAML.
* Weekly retrain workflow `.github/workflows/nightly_retrain.yml` runs every Monday 09:00 UTC.
* Drift alert: Slack ping if AUC ↓ > 0.03 or KS > 0.05.

## Data ingest v2
`code_data_ingest_statcast_v2.py`
```bash
python code_data_ingest_statcast_v2.py --season 2025
python code_data_ingest_statcast_v2.py --days 90


`code_data_ingest_statcast_v2.py`
```bash
python code_data_ingest_statcast_v2.py --season 2025
python code_data_ingest_statcast_v2.py --days 90



`train_hit_prob_v2.py`
```bash
python train_hit_prob_v2.py --days 90 --grid
Outputs model_assets/model_v2.pkl.
`train_hit_prob_v2.py`
```bash
python train_hit_prob_v2.py --days 90 --grid
Outputs model_assets/model_v2.pkl.
### Model v2 training
\`train_hit_prob_v2.py\`

    python train_hit_prob_v2.py --days 90 --grid

Outputs \`model_assets/model_v2.pkl\`.
