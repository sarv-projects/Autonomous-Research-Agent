# Autonomous Research Agent — PowerShell install (Windows)
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Autonomous Research Agent install (PowerShell)"
Write-Host "    repo: $Root"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "==> uv not found; install from https://docs.astral.sh/uv/"
    Write-Host "    irm https://astral.sh/uv/install.ps1 | iex"
    exit 1
}

Write-Host "==> Creating venv + syncing dependencies"
uv venv
uv sync

if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "==> Created .env from .env.example — edit keys as needed"
    } else {
        Write-Host "==> Warning: no .env.example found"
    }
} else {
    Write-Host "==> .env already exists (left unchanged)"
}

Write-Host "==> Offline gateway tests"
uv run python test_gateway.py

Write-Host ""
Write-Host "Done."
Write-Host ""
Write-Host "  Built today (needs GROQ_API_KEY or OPENAI/OPENROUTER + TAVILY_API_KEY):"
Write-Host '    uv run python main.py "your research topic"'
Write-Host "    uv run python main.py --history"
Write-Host "    uv run python -m src.dashboard --port 8080"
Write-Host ""
Write-Host "  Spec target (not implemented yet): chat / doctor / OpenCode free empty-key"
Write-Host "  Docs: docs/INSTALL.md · docs/SPEC.md · docs/AUDIT.md"
