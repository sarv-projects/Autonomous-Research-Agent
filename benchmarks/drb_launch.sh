#!/usr/bin/env bash
# Launch the full 100-task DeepResearch Bench run detached (resumable).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="${MODE:-standard}"
LOGDIR="benchmarks/logs"
mkdir -p "$LOGDIR"

setsid nohup uv run python benchmarks/drb_run.py --mode "$MODE" \
  > "$LOGDIR/drb_full_run.log" 2>&1 < /dev/null &
disown

echo "launched pid=$! mode=$MODE"
sleep 20
echo '--- progress ---'
if [ -f "$LOGDIR/drb_full_run.log" ]; then
  grep -E 'DRB task|ok ·|ERROR' "$LOGDIR/drb_full_run.log" | tail -5
fi
echo "done: $(wc -l < research/deep_research_bench/data/test_data/raw_data/providence.jsonl 2>/dev/null || echo 0)/100 tasks"
