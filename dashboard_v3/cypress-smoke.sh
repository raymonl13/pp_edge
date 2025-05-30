#!/usr/bin/env bash
set -euo pipefail
pkill -f uvicorn || true
pkill -f vite || true
uvicorn dashboard_v3.server:app --port 8000 --reload &
SERVER_PID=$!
wait-on --timeout 20000 http-get://localhost:8000/api/edges
npm run dev --prefix dashboard_v3 &
VITE_PID=$!
wait-on --timeout 20000 http-get://localhost:5173
npm run cy:headless --prefix dashboard_v3
kill $VITE_PID $SERVER_PID
