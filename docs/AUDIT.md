# Deep audit report

**Date:** 2026-08-08  
**Scope:** Specs vs code, cross-doc consistency, live provider probes, gateway tests.

---

## Verdict

| Area | Status |
|------|--------|
| **Documentation set** (SPEC / ARCHITECTURE / PROVIDERS / …) | Internally consistent as a **target** product |
| **Gateway unit tests** | **9/9 pass** |
| **Code vs docs** | **Gaps** — many SPEC features not implemented yet |
| **Live OpenCode free** | **Most free models still work without key**; one free model currently broken upstream |

**Bottom line:** Specs are the correct *design*. The *running prototype* is still: LangGraph + Tavily + gateway (Groq/OpenAI/OpenRouter **keys required**). Do not treat Phase A–H as shipped.

---

## 1. What the code actually does today

| Component | Implemented? | Notes |
|-----------|--------------|--------|
| LangGraph research (9 nodes) | ✅ | `parse → plan → search → extract → dedupe → analyze → evaluate ↺ → synthesize → export` |
| Max research loops | ✅ | Hard cap **3** (`MAX_ITERATIONS`) |
| Tavily search + extract | ✅ | Needs `TAVILY_API_KEY` |
| Gateway (circuit, retry, rate limit, cost, metrics) | ✅ | `src/gateway/` |
| Dashboard `/metrics` | ✅ | `src/dashboard` |
| Offline gateway tests | ✅ | `test_gateway.py` 9/9 |
| Multi-provider env | ⚠️ Partial | **Only** Groq / OpenAI / OpenRouter if **keys present** |
| OpenCode free (empty URL/key) | ❌ | Not wired; empty keys → **no routes registered** |
| Claude / Gemini / NIM / DeepSeek / Cohere adapters | ❌ | Spec only |
| Chat CLI (`main.py chat`) | ❌ | Spec only |
| `doctor` / `eval` commands | ❌ | Spec only |
| RAG / LanceDB / Qdrant | ❌ | Spec only |
| Progressive section write + citation ship-gate | ❌ | Single `call_llm` dump for full report |
| Self-improve vault / traces / strategy | ❌ | Only JSON history `~/.xiarch_memory.json` |
| MCP / Firecrawl / Exa / Wikipedia | ❌ | Spec only |
| MinerU / Nougat | ❌ | Spec only (Phase D) |
| Web product UI | ❌ | Only ops dashboard |
| YOLO | ❌ | Nowhere in repo |

---

## 2. Live OpenCode Zen probe (re-checked this audit)

`POST https://opencode.ai/zen/v1/chat/completions` **with no API key**:

| Model ID | Result |
|----------|--------|
| `big-pickle` | ✅ 200 |
| `deepseek-v4-flash-free` | ✅ 200 |
| `mimo-v2.5-free` | ✅ 200 |
| `nemotron-3-ultra-free` | ✅ 200 |
| `laguna-s-2.1-free` | ✅ 200 |
| `north-mini-code-free` | ⚠️ **401** upstream (`Provider returned error`) — flaky/broken **today** |
| Paid e.g. `kimi-k2.5` no key | ❌ 401 `Missing API key` (expected) |

`GET /zen/v1/models` — ✅ 200.

**Doc fix:** Free open path is still real for several models; do not claim *all* free IDs always work. Prefer defaults: `deepseek-v4-flash-free`, `big-pickle`, `mimo-v2.5-free`. Treat `north-mini-code-free` as optional until stable.

---

## 3. Provider catalog accuracy (docs vs official)

| Claim | Verdict |
|-------|---------|
| DeepSeek models = `deepseek-v4-flash` / `deepseek-v4-pro` | ✅ Matches official docs |
| Not `deepseek-chat` / `deepseek-reasoner` as current defaults | ✅ Correct warning |
| NVIDIA base `https://integrate.api.nvidia.com/v1` | ✅ Matches NVIDIA LLM API docs |
| OpenRouter `https://openrouter.ai/api/v1` | ✅ |
| Claude = Messages API + `x-api-key` | ✅ |
| Gemini OpenAI-compat base | ✅ Google docs |
| Groq base `https://api.groq.com/openai/v1` | ✅ |
| Groq model ids `openai/gpt-oss-20b` etc. | ✅ Groq models table |
| **Code** uses model id `gpt-oss-20b` (no `openai/` prefix) | ⚠️ May work via alias or may fail on Groq — **verify with live key**; Groq docs list `openai/gpt-oss-20b` |
| North Mini not on Cohere Platform models page | ✅ |
| Cohere Platform `/v2/chat` | ✅ |
| MinerU primary / Nougat optional | ✅ Sound; not in code yet |
| Nougat weights CC-BY-NC | ✅ Nougat README |

**Code leftover:** `src/gateway/providers.py` pricing still lists `deepseek-chat` — outdated label only (not used as default model).

---

## 4. Cross-doc consistency

| Check | Status |
|-------|--------|
| SPEC R1–R13 ↔ ARCHITECTURE | ✅ Aligned |
| ROADMAP phases A–H ↔ SPEC deferred list | ✅ Aligned |
| MinerU/Nougat in SPEC + ARCHITECTURE + ROADMAP | ✅ Aligned |
| PROVIDERS DeepSeek v4 | ✅ Aligned |
| INDEX points to final docs | ✅ |
| Redirect stubs for old files | ✅ |

| Overclaim (docs/scripts vs code) | Severity |
|----------------------------------|----------|
| “Empty LLM keys → OpenCode free works” **in current app** | **High** — only true *after* Phase A |
| install scripts / INSTALL: `main.py doctor` / `chat` | **High** — commands **do not exist** yet |
| README “self-improving… progressive reports” as product | **Medium** — target voice; “today’s CLI” section helps but lead blurb overclaims |
| `call_llm_strong` for synthesis | **Low** — `synthesize_report` uses `call_llm` not strong tier |

---

## 5. Gateway / infra correctness

| Check | Status |
|-------|--------|
| Circuit, rate limit, failover unit tests | ✅ 9/9 |
| Always sends `Authorization: Bearer …` (even empty) | ⚠️ OK for many free Zen models; empty Bearer still 200; Phase A should **omit** header when key empty (cleaner) |
| Register provider only if keys exist | ✅ Current code; blocks keyless Zen until Phase A |
| `requires-python >= 3.14` | ✅ In pyproject (environment-dependent) |
| Dependencies: groq, langgraph, dotenv, tavily | ✅ No LanceDB/MCP/MinerU deps yet (correct for light install) |

---

## 6. Security / licenses (notes)

- Nougat **weights** CC-BY-NC → commercial deploy must avoid or license separately  
- Free Zen models may use data for training (per OpenCode privacy notes) — document for users  
- No YOLO in tree  

---

## 7. Corrections applied after this audit

See git/docs updates in same session:

1. README + INSTALL + `.env.example` — clear **Built today vs Target**  
2. install scripts — only invoke **existing** commands  
3. PROVIDERS.md — free-model probe status; North Mini free flaky note  
4. Default free model recommendations  
5. Pricing table: remove obsolete `deepseek-chat` as if current  

---

## 8. Recommended next engineering (unchanged priority)

1. **Phase A** — key-optional OpenCode free default + `doctor`
2. **Phase B** — RAG
3. **Phase C** — multi-iter + progressive write + citations
4. **Phase C2** — Thinker agent (Gemini free)
5. **Phase C3** — Temporal integration (durable execution)
6. **Phase D** — tools + MinerU
7. **Phase E** — Bias mitigation (Triangulator agent)
8. **Phase F** — Factoid extraction pipeline (token optimization)
9. **Phase G** — Retriever Guard (source verification)
10. **Phase L** — Mathematical rendering

See [ROADMAP.md](ROADMAP.md) for complete phased implementation plan including new advanced capabilities.

Until A ships, operators need **GROQ_API_KEY** (or OpenAI/OpenRouter) + **TAVILY_API_KEY** for a live research run.
