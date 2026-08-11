# Installation

Supports **Bash (Linux/macOS)** and **PowerShell (Windows)**.  
Product overview: [../README.md](../README.md). Status: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

---

## Prerequisites

| Tool | Notes |
|------|--------|
| **Python** | 3.10+ (see `pyproject.toml`) |
| **uv** | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| **Git** | Clone |
| **Node 18+** (optional) | Frontend UI |
| **Keys (recommended for A4 quality)** | `GROQ_API_KEY` + `EXA_API_KEY` + `GEMINI_API_KEY` |
| **Keys (minimum free path)** | None — OpenCode Zen free + Wikipedia / built-in scrape |
| **Temporal** (optional) | Ultra-long durable runs — [TEMPORAL.md](TEMPORAL.md) |

---

## Bash (Linux / macOS)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if needed

git clone https://github.com/sarv-projects/Autonomous-Research-Agent.git
cd Autonomous-Research-Agent
bash scripts/install.sh
cp .env.example .env
# edit .env — add GROQ_API_KEY, EXA_API_KEY, GEMINI_API_KEY for best quality

uv run python main.py doctor
uv run python main.py research "your research topic" --mode deep
```

Web UI:

```bash
bash scripts/start-dev.sh
# API :8000 · UI :3000
```

---

## PowerShell (Windows)

```powershell
# install uv if needed: https://docs.astral.sh/uv/
git clone https://github.com/sarv-projects/Autonomous-Research-Agent.git
cd Autonomous-Research-Agent
.\scripts\install.ps1
copy .env.example .env
# edit .env

uv run python main.py doctor
uv run python main.py research "your research topic" --mode deep
```

---

## Environment variables (common)

| Variable | Role |
|----------|------|
| `GROQ_API_KEY` | Primary fast/strong generation (recommended) |
| `EXA_API_KEY` | Primary neural web search |
| `GEMINI_API_KEY` | Parallel scout (Flash-Lite class) |
| `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` | Optional failover |
| `FIRECRAWL_API_KEY` / `TAVILY_API_KEY` | Optional search/extract |
| `EMBEDDING_API_KEY` | Better vectors than local Dummy/BoW |

See [PROVIDERS.md](PROVIDERS.md) and `config/providers.yaml`.

---

## Verify

```bash
uv run python main.py doctor
uv run python main.py research "RAG hallucination reduction" --mode quick
```

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| No search results | Set `EXA_API_KEY` or other search keys |
| Slow / weak text | Prefer Groq over free Zen alone |
| Gemini 429 | Scout is 3 parallel calls; free tier ~15 RPM — wait and retry |
| Frontend 404 on API | Backend on :8000; `next.config.js` rewrites `/api/*` |
