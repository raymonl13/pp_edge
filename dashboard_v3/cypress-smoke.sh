#!/usr/bin/env bash
set -euo pipefail
<<<<<<< Updated upstream
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
=======

pkill -f uvicorn || true
pkill -f vite    || true

python -m uvicorn dashboard_v3.server:app --port 8000 --reload & API_PID=$!
npm --prefix dashboard_v3 run dev -- --port 5173 --strictPort & VITE_PID=$!

npx wait-on http-get://localhost:8000/api/edges
npx wait-on http://localhost:5173

npm --prefix dashboard_v3 run cy:headless

kill $API_PID $VITE_PID
>>>>>>> Stashed changes
