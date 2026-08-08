# Research notes (archive)

Background research that informed [SPEC.md](SPEC.md) and [ARCHITECTURE.md](ARCHITECTURE.md).  
**Not normative** — the SPEC wins on conflicts.

**Research date:** 2026-08

---

## Reference systems studied

| Project | Stars (approx) | Patterns adopted |
|---------|----------------|------------------|
| [Hyperresearch](https://github.com/jordan-gibbs/hyperresearch) | ~1.6k | Vault, tiers/gears, critics + patch-not-regen, cite-check, gap-fill |
| [DeerFlow 2.0](https://github.com/bytedance/deer-flow) | ~80k | Harness + skills, progressive context, MCP, chat-first surface |
| [last30days-skill](https://github.com/mvanhorn/last30days-skill) | ~58k | Multi-source fan-out, recency scoring, free sources first, doctor |
| [STORM](https://github.com/stanford-oval/storm) | ~31k | Perspectives, outline-first, VectorRM/RAG, Co-STORM mind map |
| [Tongyi DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) | ~20k | ReAct, iterative heavy mode, context summarization |
| [MiroThinker](https://github.com/MiroMindAI/MiroThinker) | ~8k | Interactive scaling (more tools > more tokens), trace collection |
| [Enterprise Deep Research](https://github.com/SalesforceAIResearch/enterprise-deep-research) | ~1.2k | Planner + reflection, MCP registry, specialized search tools |
| [BrowserPilot](https://github.com/ai-naymul/BrowserPilot) | ~0.2k | Browser escalation for blocked pages only |

---

## OpenCode Zen / Go (provider UX)

- Zen docs: curated gateway; free models listed as Free pricing  
- **Live probe:** free models on `https://opencode.ai/zen/v1/chat/completions` work **without API key**  
- Paid models without key → `401 Missing API key`  
- Go: `https://opencode.ai/zen/go/v1` subscription endpoints  
- UX model: empty URL = free Zen; arbitrary URL + optional key for anything else  

---

## Provider doc corrections

| Assumption | Official correction |
|------------|---------------------|
| DeepSeek `chat` / `reasoner` | Current API: **`deepseek-v4-flash`**, **`deepseek-v4-pro`** only ([api-docs.deepseek.com](https://api-docs.deepseek.com/)) |
| North Mini Code on Cohere Platform | **Not** on [docs.cohere.com models](https://docs.cohere.com/docs/models); use Zen `north-mini-code-free` or OpenRouter `cohere/north-mini-code:free`; Platform uses Command via `/v2/chat` |
| Cohere chat | `POST https://api.cohere.com/v2/chat` + native document citations |
| NVIDIA NIM | `https://integrate.api.nvidia.com` + `/v1/chat/completions` |
| Groq | `https://api.groq.com/openai/v1` |
| Gemini OpenAI-compat | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Claude | `https://api.anthropic.com` Messages API + `x-api-key` |

Authoritative tables: [PROVIDERS.md](PROVIDERS.md).

---

## Document parsers (checked 2026-08)

### [Nougat](https://github.com/facebookresearch/nougat) (Meta / facebookresearch) · ~10k★

- **What:** Neural PDF → Markdown for **academic** papers (LaTeX math + tables).  
- **Paper:** arXiv:2308.13418  
- **Install:** `pip install nougat-ocr` · CLI `nougat file.pdf -o out/` · optional API `nougat_api`  
- **Strengths:** Excellent on arXiv-like English scientific PDFs with formulas.  
- **Limits:** Best on scientific English; CJK/RU/JP poor; needs GPU for practical speed; **weights CC-BY-NC** (non-commercial).  
- **Last push:** 2025-02 (slower maintenance vs MinerU).  
- **Our use:** Optional specialist when `source_type=academic_pdf` and math-heavy.

### [MinerU](https://github.com/opendatalab/MinerU) (OpenDataLab) · ~77k★

- **What:** High-accuracy **document parsing engine for LLM / RAG / agents**.  
- **Formats:** PDF, DOCX, PPTX, XLSX, images, web pages → structured Markdown / JSON.  
- **Engines:** `pipeline` (CPU/GPU, stable), `vlm-engine`, `hybrid-engine`; OCR 109 languages; formulas→LaTeX, tables→HTML.  
- **Integration:** MCP Server, LangChain/Dify/FastGPT, CLI, REST (`mineru-api`), Docker, router multi-GPU.  
- **License:** Custom open license based on Apache 2.0 (as of 3.1 — check LICENSE.md).  
- **Actively maintained** (2026 releases 3.x).  
- **Our use:** **Default** document parser before RAG ingest.

**Decision:** MinerU primary · Nougat optional academic niche · never both on every page by default (cost/latency).

---

## Product conclusions

1. Web primary, CLI secondary; desktop later  
2. Multi-iter RAG research + progressive section write + mandatory citations  
3. Self-improve (vault/traces/strategy) is core, not a plugin  
4. Universal providers with empty = free Zen  
5. Evals multi-layer from day one of engine work  
6. Vector: LanceDB local, Qdrant prod  
7. Defer STORM fleet / K8s until engine quality is proven  

---

## External links

- OpenCode Zen: https://opencode.ai/docs/zen/  
- OpenCode Go: https://opencode.ai/docs/go/  
- OpenCode Providers: https://opencode.ai/docs/providers/  
- DeepSeek API: https://api-docs.deepseek.com/  
- Cohere models: https://docs.cohere.com/docs/models  
- NVIDIA NIM LLM APIs: https://docs.api.nvidia.com/nim/reference/llm-apis  
- OpenRouter: https://openrouter.ai/docs/quickstart  
- Groq OpenAI compat: https://console.groq.com/docs/openai  
- Gemini OpenAI compat: https://ai.google.dev/gemini-api/docs/openai  
- Claude models: https://platform.claude.com/docs/en/about-claude/models/overview  
