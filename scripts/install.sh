#!/usr/bin/env bash
# Providence — Bash install (Linux/macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Providence install (Bash)"
echo "    repo: $ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv not found; install from https://docs.astral.sh/uv/"
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo "==> Creating venv + syncing dependencies"
uv venv
uv sync

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "==> Created .env from .env.example — edit keys as needed"
  else
    echo "==> Warning: no .env.example found"
  fi
else
  echo "==> .env already exists (left unchanged)"
fi

echo "==> Offline gateway tests"
uv run python test_gateway.py

echo ""
echo "Done."
echo ""
echo "  Getting started:"
echo "    uv run python main.py doctor"
echo "    uv run python main.py research \"your research topic\""
echo "    uv run python main.py chat"
echo "    uv run python main.py --history"
echo "    uv run python -m src.dashboard --port 8080"
echo ""
echo "  Docs: docs/INSTALL.md · docs/SPEC.md · docs/AUDIT.md"
