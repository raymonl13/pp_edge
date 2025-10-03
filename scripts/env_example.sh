#!/usr/bin/env bash
# Local smoke only — never commit real keys
export ROUTER_SOURCE=http
export ROUTER_URL='https://api.prizepicks.com/projections?league_id=2&per_page=5000&date={date}&state_code=CO'
export ROUTER_API_KEY='REDACTED_xxxxxxxxxxxx'
export ROUTER_MIN_ROWS=30
export ROUTER_MAX_ATTEMPTS=4
export ROUTER_TIMEOUT=12
# Optional: speed up CI diagnostics (no sleep between retries)
# export ROUTER_BACKOFF_DISABLE=1
