#!/usr/bin/env bash
set -e
npm run build:preview
npx vite preview --port 5173 --strictPort &
PREVIEW=\$!
npx wait-on http://localhost:5173/
npm run cy:headless
kill \$PREVIEW
