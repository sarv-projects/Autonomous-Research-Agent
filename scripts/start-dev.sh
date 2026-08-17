#!/usr/bin/env bash
# Start API + Next.js frontend for local development.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8001}"
echo "==> Providence — dev stack"
echo "    API:      http://localhost:${PORT}/docs"
echo "    Frontend: http://localhost:3000"
echo ""

if ! command -v uv > /dev/null 2>&1; then
  echo "uv not found — https://docs.astral.sh/uv/"
  exit 1
fi

# Kill any stale process already holding the API port
if lsof -ti ":${PORT}" > /dev/null 2>&1; then
  echo "==> Port ${PORT} in use — killing stale process..."
  kill -9 $(lsof -ti ":${PORT}") 2>/dev/null || true
  sleep 0.5
fi

# Backend
PORT="$PORT" uv run python main.py server &
API_PID=$!

cleanup() {
  echo ""
  echo "Stopping API (pid $API_PID)..."
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Frontend
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  echo "==> npm install"
  npm install
fi
npm run dev
