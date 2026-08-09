# Implementation & System Audit Notes

This document provides a realistic overview of completed components, ongoing work, and known limitations within the codebase.

---

## 📊 Summary Overview

- **Core Multi-Agent Engine**: Functional (LangGraph orchestration of Planner, Researcher, Critic, Synthesizer, Compiler, Thinker, Triangulator).
- **LLM Resiliency Gateway**: Functional (Circuit breakers, token-bucket rate limiting, provider failover chain to OpenCode Zen free fallback).
- **Web UI & API**: Functional (Next.js 14 frontend + FastAPI REST endpoints with SSE streaming).
- **Evaluation System**: Functional (CLI runner for component and system evaluation suites).
- **Temporal Durable Execution**: Foundation implemented (workflows and activities defined; requires a running Temporal server for production deployment).
- **Document Parsing (PDF/Complex Docs)**: Pending (MinerU and Nougat adapters not yet implemented).

---

## 🔍 Detailed Component Audit

### 1. Multi-Agent Flow (`src/engine/agents/`)
- **Planner** (`planner.py`): Generates structured research plans, subtopic breakdown, and initial queries.
- **Researcher** (`researcher.py`): Executes iterative search and claim extraction using Tavily, Wikipedia, or built-in scrapers.
- **Critic** (`critic.py`): Evaluates section coverage and triggers research iteration loops when gaps remain.
- **Synthesizer** (`synthesizer.py`): Writes report sections progressively with inline source citation bindings.
- **Compiler** (`compiler.py`): Enforces a pre-export ship-gate (checking Sources presence and body content) and formats LaTeX math.
- **Thinker** (`thinker.py`): Provides large-context plan refinement and contradiction checking. *Note: Only invoked on `accurate` and `comprehensive` quality dials to conserve API quota.*
- **Triangulator** (`triangulator.py`): Runs parallel Pro, Con, and Neutral sub-agent calls on comparative/subjective queries, arbitrated by a Synthesis Arbiter.

### 2. LLM Gateway & Provider Routing (`src/gateway/`)
- **BYOK Architecture**: Manages provider keys with rotation, rate limits (RPM/TPM), and circuit breaker protection per model endpoint.
- **Failover Chain**: Routes requests through configured paid APIs (Groq, OpenAI, Gemini, DeepSeek) and falls back to the OpenCode Zen free endpoint when no API keys are provided.
- **Caveat**: Uptime and latency for the free fallback tier depend on upstream OpenCode Zen service availability.

### 3. RAG & Factoid Pipeline (`src/rag/`)
- **Hybrid Retrieval** (`hybrid.py`): Combines dense vector similarity and SQLite FTS5 keyword matching.
- **Factoid Extraction** (`factoid.py`): Extracts atomic factual statements from web pages before synthesis. Reduces token consumption during final report assembly; actual compression percentage varies based on source text density.
- **Retriever Guard** (`guard.py`): Scores domain reputation and filters low-scoring search results.
- **Vault** (`vault.py`): Caches retrieved sources for cross-run reuse.

### 4. Interfaces & CLI
- **Web Interface** (`frontend/` & `src/web/`): Next.js 14 app with ChatGPT-like UI, dark mode, SSE progress updates, and history view.
- **CLI Commands** (`main.py`): Supports `research`, `chat`, `doctor`, `eval`, `server`, and `--history`.

---

## 🚧 Known Gaps & Planned Enhancements

| Feature | Current Status | Planned Work |
| :--- | :--- | :--- |
| **Document Parsers** | Missing | Implement MinerU and Nougat tool adapters for complex PDF and scientific paper parsing. |
| **Temporal Approval UI** | CLI / Workflow only | Build dedicated frontend UI components for human approval step interaction in long-running workflows. |
| **Provider Management UI** | Configuration file | Add dynamic runtime provider key and route configuration forms in the web settings page. |
| **Vault Browser** | API Endpoint only | Build an interactive visual browser in the frontend for searching and inspecting cached research vault entries. |

---

## 🛠️ Verification & Testing

To verify component functionality on your local environment:

```bash
# 1. Gateway Unit Tests
uv run python test_gateway.py

# 2. Phase Integration Tests
uv run python test_phase_a.py

# 3. System Readiness Check
uv run python main.py doctor

# 4. Evaluation Benchmark Suites
uv run python main.py eval all
```
