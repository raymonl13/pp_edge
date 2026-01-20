# NBA Engine SLP — Governance

_Last updated: 2025-11-27_

This SLP describes how we evolve the NBA engine without losing context or
rebuilding the skeleton every time a chat hits a memory limit.

It applies to:

- **NBA Engine design chats** (Lane B) — this SLP is mandatory.
- **Daily SLP chats** (Lane A) — must only use Production (Lane A) scripts and behaviors.

---

## 1. Lanes

- **Lane A (Production / Daily SLP)**
  - Used for daily operational runs.
  - Only uses scripts and behaviors that have been explicitly promoted from Lane B.
  - Daily SLP chats **must not** invoke experimental scripts unless explicitly instructed
    by an Engine thread that a given change has been promoted.

- **Lane B (Experimental / Engine)**
  - Used in NBA Engine design threads.
  - Hosts new models, EV logic, filters, bankroll experiments, and roadmap evolution.
  - Nothing in Lane B is considered “live” until promotion criteria are met.

---

## 2. Dev & Shell Standards (Global PP-EDGE Rails)

All NBA Engine work (both Lane A and Lane B) **must** obey the global Shell & GitOps SLP:

- **Shell & GitOps SLP (current version):**
  - `docs/dev_slp_shell_gitops_v2025-11-28.md`
  - Key points:
    - Use **RRHM** (Rip-and-Replace Heredoc Mode) for all code handoffs:
      - `cat <<'TAG' > path/to/file` … `TAG`, then run the script separately.
    - **No notebook / Colab magics** (`%%writefile`, `!pip`, `%run`, etc.) in repo code or handoffs.
    - Use `bash` (not `zsh`) for SLP sessions, with **bracketed paste** enabled so multi-line pastes land as an editable block and only run when you press Enter.
    - Embedded Python heredocs must not contain `${VAR}`; pass data via environment variables.

- **Debugging & troubleshooting:**
  - For pipeline-level debugging, follow:
    - **PP-EDGE — Troubleshooting & Ops Playbook (v1.1)**.
  - Typical NBA debugging flow:
    - Check label coverage with `scripts/nba/report_training_days_v0.py`.
    - Use `scripts/nba/eval_slips_nba_v0.py` to examine slip legs (p_hit, edge_pp, hit).
    - Use `scripts/nba/eval_board_nba_v0.py` to examine full-board calibration.

NBA Engine chats must not violate these global rails. If a suggested command or snippet contradicts the Shell & GitOps SLP (e.g., using `%%writefile`), it should be considered invalid and corrected.

---

## 3. Phase Exit Conditions (NB-Fx)

A phase NB-Fx (e.g., NB-F1, NB-F2, etc.) is only considered **complete** when:

1. The relevant scripts and/or configs are implemented and passing basic QA on real slates.
   - “Basic QA” means:
     - The code runs successfully across at least a few real days.
     - Outputs make sense (no glaring logic bugs).
2. `docs/nba_engine_status_v0X.md` has been updated to reflect the new Lane A behavior.
3. `docs/nba_engine_roadmap_v0X.md` has been updated or superseded if the roadmap changes.
4. A git tag is created to anchor this engine state, e.g.:
   - `nba-engine-v0.1`, `nba-engine-v0.2`, etc.
   - Tag naming should align with the doc version (v0.1 → v0.1, v0.2 → v0.2, etc.).

Only after these conditions are met should the phase’s results be called “done” or be
considered for promotion to Lane A.

---

## 4. Promotion to Lane A (Daily SLP)

Promotion of any experimental behavior from Lane B → Lane A must:

1. Be explicitly documented in `docs/nba_engine_status_v0X.md`:
   - Which scripts/logic moved into Production.
   - Any changes to thresholds, EV logic, bankroll policies, etc.
2. Be linked to a specific git tag (e.g., `nba-engine-v0.2`).
3. Be communicated to Daily SLP usage as:
   - “From now on, for NBA Daily SLP, use scripts X, Y, Z for Lane A.”

Daily SLP must never “guess” what the engine does; it should always rely on:

- The Engine status doc.
- The latest tag that marks a Production state.

---

## 5. New Chat Procedure (NBA Engine Thread)

When starting a new ChatGPT **NBA Engine** conversation (due to memory limits or by choice):

1. Open the latest engine docs:
   - `docs/nba_engine_status_v0X.md`
   - `docs/nba_engine_roadmap_v0X.md`
   - `docs/nba_engine_SLP.md`

2. Paste the contents of:
   - `nba_engine_status_v0X.md`
   - `nba_engine_roadmap_v0X.md`
   - Optionally an excerpt from this SLP

   into the new chat, with a line like:

   > “This is the current NBA engine state and roadmap as of tag `nba-engine-v0.X`.  
   > Daily SLP uses Lane A only. This chat is Lane B (Engine). Follow `docs/dev_slp_shell_gitops_v2025-11-28.md` for all shell/code interactions. Let’s continue from here.”

3. Treat ChatGPT as a stateless brain:
   - It should read the docs as the source of truth.
   - It should not rely on prior chat history.
   - It should not override the repo state unless we ask it to propose changes.

---

## 6. Scope & Discipline

- **Engine design chats (Lane B)**:
  - May propose new models, EV logic, filters, bankroll strategies, and roadmap changes.
  - Must always:
    - Respect doc+tag phase exit conditions.
    - Respect the Shell & GitOps SLP and Troubleshooting Playbook.
    - Propose changes in a way that is compatible with the current repo and status docs.
  - Should clearly distinguish:
    - “We are designing NB-Fx” from “We are promoting NB-Fx to Lane A.”

- **Daily SLP chats (Lane A)**:
  - Only run the daily spine and Lane A scripts.
  - May ask for operational help (e.g., “what command do I run for Phase B today?”).
  - Should not modify engine design or scripts directly.

---

## 7. Versioning

- Document version files (`nba_engine_status_v0X.md`, `nba_engine_roadmap_v0X.md`) and tags (e.g. `nba-engine-v0.X`) must stay in sync.
  - When behavior changes in Lane A:
    - Bump the doc version (e.g., v0.1 → v0.2).
    - Create a new git tag (e.g., `nba-engine-v0.2`).
- Older docs/tags should be retained for historical context but clearly marked as superseded.

---

This SLP is meant to enforce the discipline needed to:

- Keep the NBA engine ambitious and evolving.
- Avoid “skeleton rebuild” and context loss when chats reset.
- Ensure Daily SLP is always using a well-defined, documented Production engine.
- Ensure Engine chats respect the Shell & GitOps SLP and do not regress into unsafe patterns (Colab magics, ad-hoc multi-line pastes, etc.).
