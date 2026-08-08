# Installation

Supports **Bash (Linux/macOS)** and **PowerShell (Windows)**.

For **built vs target** features, read [AUDIT.md](AUDIT.md).

---

## Prerequisites

| Tool | Notes |
|------|--------|
| **Python** | 3.14+ (`pyproject.toml`) |
| **uv** | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| **Git** | Clone repo |
| **Keys (live research today)** | At least one of `GROQ_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` **and** `TAVILY_API_KEY` |
| **Temporal Server** (optional) | For durable execution (Phase C3) - see below |
| **Ollama/vLLM** (optional) | For local factoid extraction (Phase F) - see below |

---

## Bash (Linux / macOS)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if needed

git clone <repo-url>
cd Autonomous-Research-Agent
bash scripts/install.sh
# edit .env

uv run python main.py "your research topic"
uv run python main.py --history
uv run python -m src.dashboard --port 8080
uv run python test_gateway.py
```

---

## PowerShell (Windows)

```powershell
irm https://astral.sh/uv/install.ps1 | iex   # if needed

git clone <repo-url>
cd Autonomous-Research-Agent
.\scripts\install.ps1
# edit .env

uv run python main.py "your research topic"
```

---

## Environment

Copy [`.env.example`](../.env.example) → `.env`.

| Variable | Today | Notes |
|----------|-------|--------|
| `GROQ_API_KEY` | Required* | *or* OpenAI / OpenRouter |
| `OPENAI_API_KEY` | Optional | Failover |
| `OPENROUTER_API_KEY` | Optional | Failover |
| `TAVILY_API_KEY` | Required for web search | |
| OpenCode / Claude / Gemini / NIM / … | Target Phase A | See [PROVIDERS.md](PROVIDERS.md) |
| `VECTOR_BACKEND` | Target Phase B | Unused by prototype |
| `TEMPORAL_SERVER_ADDRESS` | Phase C3 | Temporal server for durable execution |
| `OLLAMA_BASE_URL` | Phase F | Ollama server for factoid extraction |
| `VLLM_BASE_URL` | Phase F | vLLM server for factoid extraction |
| `FACTOID_MODEL` | Phase F | Model for factoid extraction (e.g., llama3:8b) |

---

## Optional: Qdrant (target)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Not used until RAG lands.

---

## Optional: Temporal Server (Phase C3)

For durable execution, crash recovery, and 24h+ research runs:

```bash
# Install Temporal CLI
curl -sSf https://temporal.io/cli.sh | sh

# Start Temporal Server (development mode)
temporal server start-dev

# Or run via Docker
docker run --rm -p 7233:7233 temporalio/auto-setup:latest
```

Set environment variable:
```bash
export TEMPORAL_SERVER_ADDRESS="localhost:7233"
```

See [ARCHITECTURE.md §8](ARCHITECTURE.md#8-temporal-integration-new---durable-execution) for details.

---

## Optional: Ollama/vLLM (Phase F)

For local factoid extraction with token optimization:

### Option 1: Ollama (easier)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model for factoid extraction
ollama pull llama3:8b
# or
ollama pull phi3

# Start Ollama server
ollama serve
```

Set environment variable:
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export FACTOID_MODEL="llama3:8b"
```

### Option 2: vLLM (faster, GPU required)

```bash
# Install vLLM
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3-8B --port 8000
```

Set environment variable:
```bash
export VLLM_BASE_URL="http://localhost:8000"
export FACTOID_MODEL="meta-llama/Meta-Llama-3-8B"
```

See [FACTOID_PIPELINE.md](FACTOID_PIPELINE.md) for details on factoid extraction.

---

## Verify (today)

```bash
uv run python test_gateway.py    # must: 9/9
uv run python main.py --history  # history CLI
# with keys: uv run python main.py "smoke test topic"
```

**Not available yet:** `main.py chat`, `main.py doctor`, `main.py eval` (roadmap).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `All LLM providers failed` / no routes | Set `GROQ_API_KEY` (or OpenAI/OpenRouter) |
| Tavily errors | Set `TAVILY_API_KEY` |
| `No module named 'src'` | Run from repo root after `uv sync` |
| Rate limits | Wait; add failover key; reduce concurrent use |
| Temporal connection failed | Ensure Temporal server is running on `localhost:7233` |
| Ollama connection failed | Ensure Ollama server is running: `ollama serve` |
| vLLM connection failed | Ensure vLLM server is running on configured port |
| Factoid extraction errors | Verify local model is downloaded: `ollama pull llama3:8b` |
| GPU out of memory for vLLM | Use smaller model or reduce batch size |
