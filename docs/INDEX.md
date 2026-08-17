# Documentation

**Providence** — cited research reports, hybrid RAG, Zen-free workhorse, Gemini thinker.

| Doc | Purpose |
|-----|---------|
| [README](../README.md) | What it is, quick start, modes, pipeline |
| [INSTALL.md](INSTALL.md) | Setup, keys, troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | As-built agents, graph, RAG, ship-gate |
| [PROVIDERS.md](PROVIDERS.md) | Zen, Gemini, optional paid endpoints |
| [GATEWAY.md](GATEWAY.md) | Gateway + ops dashboard |

## Benchmarks

| Path | What |
|------|------|
| [benchmarks/RESEARCH_BENCHMARK.md](../benchmarks/RESEARCH_BENCHMARK.md) | 15-topic scored suite |
| [benchmarks/](../benchmarks/) | Runner, scorer, logs |

## Layout

- `src/` — graph, agents, gateway, RAG, tools, API
- `frontend/` — Next.js 14
- `scripts/` — install and dev stack
- `config/` — `modes.yaml`, `providers.yaml`
- `reports/` — generated Markdown / HTML
