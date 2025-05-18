# PP-EDGE Project Guide  (v1.0 · 06-May-2025)

This file is the **canonical reference** for every ChatGPT conversation in the
“PP-EDGE v6.7 Build-Out” project.  
Keep it updated; pin the **Dashboard** chat in the sidebar for status.

---

## 📁 1 Drive / Colab folder map

/content/drive/My Drive/pp_edge/ ← ROOT
├─ code_core_pp_edge_core_v6_7_v#.py ← engine brain (imported by wrapper)
├─ code_cli_pp_edge_engine_v#.py ← CLI wrapper (never touches logic)
├─ code_cli_pp_edge_scraper_v#.py ← pulls live feeds (optional)
├─ code_utils_*_v#.py ← helper modules (bankroll, VaR…)
├─ config_pp_edge_v6.#.yaml ← ONLY source of tunables
├─ data/
│ ├─ live_feeds_YYYY-MM-DD.json ← full API dump (archived)
│ ├─ data_feed_sample.json ← 1-row sample for parser tests
│ ├─ bankroll.json ← authoritative bankroll ledger
│ └─ logs/ ← payout_refresh.log, backtests…
└─ docs_project_guide.md ← << you are here


---

## 🗂 2 Naming-prefix convention

| Prefix        | Meaning                            | Example file                               |
|---------------|------------------------------------|--------------------------------------------|
| `code_core_`  | Any module imported by the engine  | `code_core_pp_edge_core_v6_7_v2.py`        |
| `code_cli_`   | Stand-alone scripts / wrappers     | `code_cli_pp_edge_engine_v1.py`            |
| `code_utils_` | Helper libraries (bankroll, VaR)   | `code_utils_bankroll_v1.py`                |
| `config_`     | YAML configs                       | `config_pp_edge_v6.8.yaml`                 |
| `data_`       | Small sample or synthetic data     | `data_feed_sample.json`                    |
| (none)        | Large real feeds go in `/data/…`   | `data/live_feeds_2025-05-06.json`          |
| `docs_`       | Markdown docs                      | `docs_project_guide.md`                    |

---

## 🚦 3 Milestone flow (one chat each)

| ID | Chat title                 | Deliverable                              |
|----|----------------------------|------------------------------------------|
| M0 | **PP-EDGE Dashboard** (pin)| Status table & parking-lot ideas         |
| M1 | Parser Build               | `_simplify_props()` done                 |
| M2 | Bayesian Hit-Prob          | `bayes_hit_prob()` + priors validated    |
| M3 | Edge & Payout Logic        | `calc_edge()` + payouts synced           |
| M4 | Diversification & Quotas   | `build_slips()` respects YAML caps       |
| M5 | Kelly Bankroll             | `code_utils_bankroll_v1.py` + YAML hooks |
| M6 | Monte-Carlo VaR            | `code_utils_mc_var_v1.py` wired in       |
| M7 | Renderer Polish            | Pretty Markdown / JSON output            |
| M8 | Daily Runner Notebook      | `notebook_pp_edge_daily_runner.ipynb`    |

*Every chat starts with*:  We’re in “PP-EDGE v6.7”.
Files to reference: docs_project_guide.md + anything in code_core_/config_/data_.
Goal for this chat (Milestone M#): <one-liner>.
Task: <specific ask>.



---

## 🛠 4 Colab quick-start snippet

# --- Colab Session Startup (GitHub is SSOT) -----------------
from google.colab import drive
drive.mount('/content/drive')

import os, pathlib, subprocess, textwrap, sys
ROOT = pathlib.Path('/content/drive/My Drive/pp_edge')  # Drive location

if not (ROOT / '.git').exists():                       # first time only
    !git clone https://github.com/raymonl13/pp_edge.git "$ROOT"

%cd "$ROOT"
!git pull origin main                                  # always start fresh

# set PAT for push (once per VM)
!git config --global user.name  "Raymon Lacy"
!git config --global user.email "raymon@example.com"
REDACTED_TOKEN

# quick smoke test: imports + fixture files
%%bash
python - <<'PY'
import importlib, pathlib, sys, yaml
root = pathlib.Path.cwd()
sys.path.append(str(root))

mods = ["code_utils_prob_v1", "code_core_pp_edge_core_v6_7_v6"]
fix  = yaml.safe_load((root/"fixtures.yaml").read_text())
files = [root/fix["demo_slip_input"], root/fix["statcast_with_parks"]]

miss=[]
for m in mods:
    try: importlib.import_module(m)
    except Exception as e: miss.append(f"{m}: {e}")
for f in files:
    if not f.exists(): miss.append(f"missing {f}")
if miss: raise SystemExit("Smoke failed → " + "; ".join(miss))
print("Smoke OK ✓")
PY
# ------------------------------------------------------------

# optional one-liners:
# !python code_cli_pp_edge_engine_v1.py --yaml config_pp_edge_v6.8.yaml --date $(date -I)

Updated minimal macOS session-startup script
Copy the block below into a shell script (e.g. pp_edge_start.sh) or paste line-by-line in Terminal whenever you open a new session.
export ROOT=~/Desktop/pp_edge
[ -d "$ROOT/.git" ] || git clone git@github.com:raymonl13/pp_edge.git "$ROOT"
cd "$ROOT"
git pull origin main
python3 - <<'PY'
import importlib, pathlib, yaml, sys
root = pathlib.Path.cwd(); sys.path.append(str(root))
mods = ["code_utils_prob_v1","code_core_pp_edge_core_v6_7_v6"]
fx = yaml.safe_load((root/"fixtures.yaml").read_text())
files = [root/fx["demo_slip_input"], root/fx["statcast_with_parks"]]
miss=[]
for m in mods:
    try: importlib.import_module(m)
    except Exception as e: miss.append(f"{m}: {e}")
for f in files:
    if not f.exists(): miss.append(f"missing {f}")
if miss: raise SystemExit("Smoke failed → "+", ".join(miss))
print("Smoke OK ✓")
PY


Every Milestone chat should reference this section.

#	Rule / Tactic	Why it matters
1	One clone per environment. Guard with `[ -d "$ROOT/.git" ]	
2	Always git pull origin main before editing.	Keeps each local copy in sync with GitHub (SSOT) and prevents fast-forward push failures.
3	Set user.name & user.email once per VM/machine.	Prevents “Author identity unknown” commit errors.
4	Auth: SSH key on persistent laptops; PAT embedded in remote URL for ephemeral Colab VMs.	Ensures non-interactive pushes everywhere.
5	Local smoke test (smoke_local.py or heredoc) before full pytest.	1-second check for missing modules/fixtures—fast feedback.
6	CI workflow: first job = smoke, second job = full pytest.	Fail fast; clear diagnostic separation.
7	Archive protocol: move deprecated files to _archive/ **and rename test .py → .py.txt.	Prevents PyTest collecting dead tests, but keeps history for easy restore.
8	Search _archive/ before stubbing. find _archive -name missing_file	Recover real helpers/fixtures instead of duplicating work.
9	fixtures.yaml registry maps logical names to fixture paths; tests use get_fixture().	Eliminates hard-coded paths; moving data doesn’t break tests.
10	git status + git diff --cached before every commit.	Confirms intended files are staged; no surprises in commit.
11	Empty commit (git commit --allow-empty) to force a new CI run when no code changed.	Generates a new commit SHA so Actions rebuilds latest state.
12	Resolve rebase conflicts rather than force-push over main.	Keeps linear history and protects teammates’ work.
13	Colab notebook header: clone/pull → export ROOT → set PAT → run smoke test.	Deterministic VM startup; zero “file not found” surprises.
14	Document every archive/restore in docs_milestone_manifest.md.	Traceability during future sweeps & refactors.



