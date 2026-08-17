# Implementation status

**Date:** 2026-08-10  
**Version:** 0.4.0 (A4 — ultra steals)  
**Default arch:** `A4_ultra_steals` — see [ARCHITECTURE_BENCHMARKS.md](ARCHITECTURE_BENCHMARKS.md)

## Working (production-usable)

| Area | Status |
|------|--------|
| Multi-agent LangGraph research (A4) | ✅ |
| **Scout** (Exa + 3× parallel Gemini) | ✅ |
| **Devil’s-advocate gather** | ✅ |
| **Claim adjudicator** + 1 Socratic hop | ✅ |
| **Evidence Bedrock** + **Research Debt** + Sources | ✅ |
| CoVe-lite claim–evidence ship-gate | ✅ |
| Per-run RAG isolation (`run_id`) | ✅ |
| Off-topic hard fail → re-search / abort | ✅ |
| Exa primary when `EXA_API_KEY` set | ✅ |
| Groq primary workhorse (e.g. gpt-oss-120b) | ✅ |
| Zen free fallback; Gemini scout (+ thinker failover) | ✅ |
| Thinking panel (learned / gaps / next_action) | ✅ |
| Async jobs (`/api/jobs`) + progress SSE | ✅ |
| Editable plan API + UI (L1 optional / L2 required) | ✅ |
| Deep templates (exec summary, eval matrix, failure modes) | ✅ |
| Multi-pass self-critique | ✅ |
| Modes + budgets + autonomy L1–L3 | ✅ |
| Resilient LLM gateway + providers.yaml | ✅ |
| Tool bus (Wiki, Firecrawl, Exa/Tavily, arXiv) | ✅ |
| Tool bus speed: TTL search cache + parallel extraction + optional provider fusion | ✅ |
| Ops dashboard search-cache metrics (size, TTL, hit rate) | ✅ |
| Hybrid RAG (LanceDB + FTS) + on-topic vault filter | ✅ |
| FastAPI + Next.js UI | ✅ |
| Temporal optional ultra-long | ✅ |
| MIT LICENSE | ✅ |

## Latest E2E (same RAG topic)

| Metric | A0 (legacy) | A4 (current) |
|--------|-------------|--------------|
| Overall quality (rubric) | ~38% | **~87%** |
| Sources | Euler junk | **41 real URLs** |
| Claim–evidence | fail | **34/36 (94%)** |
| Euler contamination | many | **0** |
| Wall time (deep) | ~5 min | **~4.7 min** (Groq+Exa) |
| Honesty layers | none | **Bedrock + Research Debt** |

Report: `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_192307.md`  
Vs product DR: **~87% vs ChatGPT ~90% / Gemini ~88%** ([benchmarks](ARCHITECTURE_BENCHMARKS.md)).

## Optional / environment-dependent

| Area | Notes |
|------|--------|
| Exa / Tavily / Firecrawl cloud | API keys |
| Groq / Gemini quality path | Keys in `.env` |
| OpenAI embeddings | Better than BoW Dummy |
| Temporal cluster | `main.py worker` |
| Python sandbox / SymPy straitjacket | Not default (see ULTRA_ARCH_COMPARISON) |

## Intentionally not built (yet)

- GNN citation authority graph  
- Neo4j nightly consolidation  
- Paper-code re-execution sandbox  
- Multi-user SaaS auth  

## How to verify

```bash
uv run python main.py doctor
uv run python main.py research "short test topic" --mode quick
bash scripts/start-dev.sh
```
