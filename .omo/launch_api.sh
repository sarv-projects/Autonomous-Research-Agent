#!/usr/bin/env bash
# Launch the Providence API server detached on PORT (default 8124).
set -u
PORT="${PORT:-8124}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Kill any prior instance safely (bracket trick avoids self-match).
pkill -f "[m]ain.py server" 2>/dev/null
sleep 1

setsid nohup env PORT="$PORT" uv run python main.py server \
  > /tmp/prov_api.log 2>&1 < /dev/null &
disown

sleep 12
echo "procs: $(ps aux | grep -c '[m]ain.py server')"
echo '--- log ---'
tail -5 /tmp/prov_api.log
echo '--- status ---'
curl -s -m 8 "http://localhost:${PORT}/api/status" | head -c 300
echo
echo '--- root ---'
curl -s -m 8 "http://localhost:${PORT}/" | head -c 150
echo
