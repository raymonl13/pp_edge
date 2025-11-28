# NBA Engine SLP — Governance

This SLP describes how we evolve the NBA engine without losing context.

## Lanes

- **Lane A (Prod)**: what Daily SLP uses by default.
- **Lane B (Experimental)**: new models/logic/scripts tested alongside A.

## Phase Exit Conditions

A phase (NB-Fx) is only considered complete when:

1. The relevant scripts are implemented and passing basic QA on real slates.
2. `docs/nba_engine_status_v0X.md` has been updated to reflect current reality.
3. `docs/nba_engine_roadmap_v0X.md` has been updated or superseded if the roadmap changes.
4. A git tag is created (e.g., `nba-engine-v0.X`) to anchor the engine state.

## New Chat Procedure

When starting a new ChatGPT "NBA Engine" conversation:

1. Open `docs/nba_engine_status_v01.md` and `docs/nba_engine_roadmap_v01.md`.
2. Paste them at the top of the new chat with a one-liner like:
   > "This is the current NBA engine state and roadmap as of tag nba-engine-v0.1. Let's continue from here."
3. Treat the chat as a stateless brain that reads the repo; do not rely on chat history as the source of truth.

