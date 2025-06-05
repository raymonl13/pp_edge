#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────── basic setup ──────────────────────────
cd "$HOME/Desktop/pp_edge" || { echo "❌ ~/Desktop/pp_edge not found"; exit 1; }

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt

DEV_PORT=5174
API_PORT=8000

# ────────────────────── PATCHES ──────────────────────
# 1) Network-level JSON.parse guard
NET_GREP='try\s*{\s*const\s*data\s*=\s*JSON\.parse'
if ! grep -qE "$NET_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe \
's|(fetch\(.+?\)\s*\.then\()\s*res => res\.json\(\)\)|$1 async res => { try { return await res.json(); } catch (_) { return []; } }|s' \
dashboard_v3/src/components/EdgeTable.jsx
fi

# 2) Row-level safeParse guard
ROW_GREP='const safeParse'
if ! grep -q "$ROW_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe '
    s|(import .+?;\n)|$1\nconst safeParse = s => { try { return JSON.parse(s ?? "[]"); } catch { return []; } };\n|s;
    s/JSON\.parse\s*\(/safeParse(/g;
  ' dashboard_v3/src/components/EdgeTable.jsx
fi

# 3) package.json dev script uses env-port
DEV_SCRIPT_GREP='--port 5173'
if grep -q -- "$DEV_SCRIPT_GREP" dashboard_v3/package.json; then
  perl -0777 -i -pe \
's/"dev":\s*"[^"]*--port\s+5173[^"]*"/"dev\": \"vite --port \\${DEV_PORT:-5174} --strictPort\"/g' \
dashboard_v3/package.json
fi

# ────────────────────── installs & audits ──────────────────────
npm ci --prefix dashboard_v3
npm audit --prefix dashboard_v3 --audit-level=high

# ────────────────────── server startup ──────────────────────
pkill -f uvicorn || true
pkill -f vite || true
lsof -ti tcp:${API_PORT} | xargs kill -9 2>/dev/null || true   # free 8000

export PP_EDGE_TEST_MODE=1
python -m uvicorn dashboard_v3.server:app --port "$API_PORT" --reload &

DEV_PORT=$DEV_PORT npm --prefix dashboard_v3 run dev &  # relies on patched package.json

# ────────────────────── readiness gates ──────────────────────
npx wait-on --httpTimeout 30000 "http-get://localhost:${API_PORT}/api/edges"
npx wait-on --httpTimeout 30000 "http://localhost:${DEV_PORT}"

# ────────────────────── Cypress smoke ──────────────────────
(
  cd dashboard_v3
  npx cypress run \
    --config baseUrl=http://localhost:${DEV_PORT} \
    --browser electron \
    --headless
)

# ────────────────────── cleanup & commit ──────────────────────
pkill -P $$ || true

if ! git diff --cached --quiet || ! git diff --quiet; then
  git add dashboard_v3/src/components/EdgeTable.jsx dashboard_v3/package.json || true
  git commit -m "chore(phase4c): tidy script, retain guards & env-port dev script"
  git push
fi

echo "✅ Phase 4-C runner completed successfully."
#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────── basic setup ──────────────────────────
cd "$HOME/Desktop/pp_edge" || { echo "❌ ~/Desktop/pp_edge not found"; exit 1; }

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt

DEV_PORT=5174
API_PORT=8000

# ────────────────────── PATCHES ──────────────────────
# 1) Network-level JSON.parse guard (existing)
PATCH_GREP='try\s*{\s*const\s*data\s*=\s*JSON\.parse'
if ! grep -qE "$PATCH_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe \
's|(fetch\(.+?\)\s*\.then\()\s*res => res\.json\(\)\)|$1 async res => { try { return await res.json(); } catch (_) { return []; } }|s' \
dashboard_v3/src/components/EdgeTable.jsx
fi

# 2) Row-level safeParse guard (NEW)
ROW_PATCH_GREP='const safeParse'
if ! grep -q "$ROW_PATCH_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe '
    s|(import .+?;\n)|$1\nconst safeParse = s => { try { return JSON.parse(s ?? "[]"); } catch { return []; } };\n|s;
    s/JSON\.parse\s*\(/safeParse(/g;
  ' dashboard_v3/src/components/EdgeTable.jsx
fi

# --- Patch package.json dev script (NEW) -------------------------------------
DEV_SCRIPT_GREP='--port 5173'
if grep -q -- "$DEV_SCRIPT_GREP" dashboard_v3/package.json; then
  perl -0777 -i -pe 's/"dev":\s*"[^"]*--port\s+5173[^"]*"/"dev\": \"vite --port \${DEV_PORT:-5174} --strictPort\"/g' \
  dashboard_v3/package.json
fi

# ────────────────────── installs & audits ──────────────────────
npm ci --prefix dashboard_v3
npm audit --prefix dashboard_v3 --audit-level=high

# ────────────────────── server startup ──────────────────────
pkill -f uvicorn || true
pkill -f vite || true
lsof -ti tcp:${API_PORT} | xargs kill -9 2>/dev/null || true   # free 8000

export PP_EDGE_TEST_MODE=1
python -m uvicorn dashboard_v3.server:app --port "$API_PORT" --reload &

DEV_PORT=$DEV_PORT npm --prefix dashboard_v3 run dev &  # relies on patched package.json

# ────────────────────── readiness gates ──────────────────────
npx wait-on --httpTimeout 30000 "http-get://localhost:${API_PORT}/api/edges"
npx wait-on --httpTimeout 30000 "http://localhost:${DEV_PORT}"

# ────────────────────── Cypress smoke ──────────────────────
(
  cd dashboard_v3
  npx cypress run \
    --config baseUrl=http://localhost:${DEV_PORT} \
    --browser electron \
    --headless
)

# ────────────────────── cleanup & commit ──────────────────────
pkill -P $$ || true

if ! git diff --cached --quiet || ! git diff --quiet; then
  git add dashboard_v3/src/components/EdgeTable.jsx dashboard_v3/package.json dashboard_v3/package-lock.json || true
  git commit -m "chore(phase4c): safeParse row guard + env-port dev script + smoke hardening"
  git push
fi

echo "✅ Phase 4-C runner completed successfully."
#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Desktop/pp_edge" || { echo "❌ ~/Desktop/pp_edge not found"; exit 1; }

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt

DEV_PORT=5174
API_PORT=8000

PATCH_GREP='try\s*{\s*const\s*data\s*=\s*JSON\.parse'
# --- Patch EdgeTable.jsx network JSON.parse (existing) -----------------------
PATCH_GREP='try\s*{\s*const\s*data\s*=\s*JSON\.parse'
if ! grep -qE "$PATCH_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe '...original one-liner...' dashboard_v3/src/components/EdgeTable.jsx
fi

# --- Patch EdgeTable.jsx per-row safe JSON.parse (NEW) -----------------------
ROW_PATCH_GREP='const safeParse'
if ! grep -q "$ROW_PATCH_GREP" dashboard_v3/src/components/EdgeTable.jsx; then
  perl -0777 -i -pe '
    s|(import .+?;\n)|$1\nconst safeParse = s => { try { return JSON.parse(s ?? "[]"); } catch { return []; } };\n|s;
    s/JSON\.parse\s*\(/safeParse(/g;
  ' dashboard_v3/src/components/EdgeTable.jsx
fi

# --- Patch package.json dev script (NEW) -------------------------------------
DEV_SCRIPT_GREP='--port 5173'
if grep -q "$DEV_SCRIPT_GREP" dashboard_v3/package.json; then
  perl -0777 -i -pe 's/"dev":\s*"[^"]*--port\s+5173[^"]*"/"dev\": \"vite --port \${DEV_PORT:-5174} --strictPort\"/g' dashboard_v3/package.json
fi

npm ci --prefix dashboard_v3
npm audit --prefix dashboard_v3 --audit-level=high

pkill -f uvicorn || true
pkill -f vite || true

export PP_EDGE_TEST_MODE=1
python -m uvicorn dashboard_v3.server:app --port "$API_PORT" --reload &
npm --prefix dashboard_v3 run dev -- --port "$DEV_PORT" --strictPort &

npx wait-on --httpTimeout 30000 "http-get://localhost:${API_PORT}/api/edges"
npx wait-on --httpTimeout 30000 "http://localhost:${DEV_PORT}"

(
  cd dashboard_v3
  npx cypress run \
    --config baseUrl=http://localhost:${DEV_PORT} \
    --browser electron \
    --headless
)
pkill -P $$ || true

if ! git diff --cached --quiet || ! git diff --quiet; then
  git add dashboard_v3/src/components/EdgeTable.jsx dashboard_v3/package-lock.json || true
  git commit -m "chore(phase4c): robust JSON parsing + deterministic deps + smoke hardening"
  git push
fi

echo "✅ Phase 4-C runner completed successfully."

