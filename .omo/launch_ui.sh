#!/usr/bin/env bash
# Launch the Providence Next.js dev server detached, proxying to the API backend.
set -u
PORT="${PORT:-3000}"
BACKEND="${BACKEND_URL:-http://localhost:8124}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"

pkill -f "[n]ext dev" 2>/dev/null
sleep 2

setsid nohup env BACKEND_URL="$BACKEND" npx next dev -p "$PORT" \
  > /tmp/prov_ui.log 2>&1 < /dev/null &
disown

sleep 15
echo '--- ui log ---'
tail -6 /tmp/prov_ui.log
echo '--- ui up ---'
curl -s -m 10 -o /dev/null -w 'http=%{http_code}\n' "http://localhost:${PORT}/"
echo '--- rewrite test ---'
curl -s -m 10 "http://localhost:${PORT}/api/status" | head -c 220
echo
