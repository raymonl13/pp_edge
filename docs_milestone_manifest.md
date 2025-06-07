# PP-EDGE Milestone Manifest  
*(last updated 21 May 2025 – tag v8.0.0)*

| ID  | Milestone                                 | Status / Tag              | Key deliverables (headline only)                                                                                 | Carry-forward to next milestone |
|-----|-------------------------------------------|---------------------------|------------------------------------------------------------------------------------------------------------------|---------------------------------|
| M0  | Project Dashboard & Parking-Lot           | ✅ v0.1                   | Status table, file-panel convention                                                                              | — |
| M1  | Parser Build                              | ✅ v1.0                   | `simplify_props()` implementation; first core/cli scaffold                                                       | — |
| M2  | Bayesian Hit-Probability v0               | ✅ v2.3                   | `bayes_hit_prob`, prior tuning, unit tests                                                                       | Superseded by ML v1 |
| M3  | Edge & Payout Logic                       | ✅ v3.4                   | `calc_edge()`, payout scraper, site sync                                                                        | — |
| M4  | Diversification & Quotas                  | ✅ v4.8                   | `build_slips()`, YAML stake caps, Demon/Goblin tiers                                                             | revisit after Tier analytics |
| M5  | Kelly Bankroll (core math)                | ✅ v5.0                   | `code_utils_bankroll_v1.py`, bankroll YAML hooks                                                                 | Monte-Carlo sim (done M6) |
| M5A | ML Plumbing for Hit-Prob v1               | ✅ commit `dc7a54f`       | Stubs, CI green, core imports switched                                                                           | — |
| M5B | Feature realism & ML integration          | ✅ commit `f0986b2`       | Edge-filter, PriceFix ingest, edge-sheet driver                                                                  | Nightly cron (done M6) |
| M6  | Bankroll & Dashboard foundation           | ✅ v6.7.1                 | travel-miles feature, Monte-Carlo sim, scenario replay, tier sizing, nightly cron, dashboard v2                  | Slip-builder, alerting (done M7) |
| M7  | Slip Builder & Tier Tagging               | ✅ v7.0.0                 | SlipBuilder v2, Demon/Goblin stake caps, dry-run submit CLI, dashboard filters + P/L, webhook alerting           | Live submit flow (done M8) |
| M8  | Live Submit & Tier Analytics              | ✅ v8.0.0                 | Live-submit CLI, result poller, tier analytics, dashboard v3, stub-audit job, 80 % coverage gate                 | **Model retraining & calibration** |
| M9  | Model Retraining & Calibration            | ⏳ pending                | Statcast 2026 ingest, LightGBM v2, isotonic/Platt scaling, weekly retrain workflow, dashboard v4 calibration plot | — |


Milestone 5B – done ✅ (commit PLACEHOLDER_SHA)
Carry-forward to M6:
* Monte-Carlo bankroll sizing
* Scenario simulator vs historical edge sheets
* Tier-based bankroll diversification
* Nightly cron job to auto-publish edge sheet
* Streamlit dashboard for next-day board

### v7.0.0  — Slip Builder · Tier Stake · Alerting  (2025-05-23)
- Phase 1 SlipBuilder v2
- Phase 2 Bankroll stakes & caps
- Phase 3 submit_slips dry-run CLI
- Phase 4 Dashboard filters + P/L
- Phase 5 Webhook alerting & travel_miles
🔍 Milestone-10 wrap-up — final validation
Check	My review	OK?
CI & Coverage badge green on main @ v0.10.0, fail-under now 60 % scoped to internal pkgs	confirms in Actions UI	✅
model_assets/ tracked with .gitkeep; checksum guard for calibration_params_v2.yaml in CI	directory present, SHA-256 step passes	✅
Vendored cruft purged (node_modules, screenshots) & .gitignore hardened	repo size shrink verified by git-sizer	✅
Double on-push workflows removed?	one duplicate still remains (nightly_retrain.yml also triggers on push)	⚠️ fix in Milestone 11 Phase 1-A
docs_milestone_manifest.md row for M10 ✅ & “M11 ⏳” placeholder	ready to copy below	✅
Panel slots 18 / 20 after node purge	2 free for M11 files	✅

No red flags beyond the duplicate workflow trigger.



| M10 | Infra unfreeze & dashboard smoke | ✅ v0.10.0 | commit 1a7069b |
| M11 | Coverage & CI hardening | ⏳ pending | raise gate, e2e pack, docs pass | — |
