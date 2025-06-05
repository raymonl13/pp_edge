#!/usr/bin/env bash
set -euo pipefail
pkill -f uvicorn || true
pkill -f vite    || true

python -m uvicorn dashboard_v3.server:app --port 8000 --reload & API_PID=$!
npm --prefix dashboard_v3 run dev -- --port 5173 --strictPort & VITE_PID=$!


npx wait-on http-get://localhost:8000/api/edges
npx wait-on http://localhost:5173    # GET is fine for Vite root

npm --prefix dashboard_v3 run cy:headless
kill $API_PID $VITE_PID
