# LLM providers

**Rule:** official docs + live `GET /models` only. Do not invent model IDs.

Related: [ARCHITECTURE.md](ARCHITECTURE.md) · [INSTALL.md](INSTALL.md)

---

## How Providence uses models

| Tier | Role | Default |
|------|------|---------|
| **fast** | Planner, critic, claim extract | OpenCode Zen free |
| **strong** | Synthesis / section writing | OpenCode Zen free |
| **thinker** | Scout, plan refine, contradictions, search strategy | **Gemini Flash only** |

Configured in `config/providers.yaml`. Empty `base_url` → Zen. Empty `api_key_env` → no `Authorization` header.

---

## OpenCode Zen (default workhorse)

| | |
|--|--|
| Docs | [opencode.ai/docs/zen](https://opencode.ai/docs/zen/) |
| Base | `https://opencode.ai/zen/v1` |
| Chat | `POST /chat/completions` |
| Models | `GET https://opencode.ai/zen/v1/models` |
| Free auth | **none** |
| Paid / Go | `OPENCODE_API_KEY` — Go is `https://opencode.ai/zen/go/v1` (never free) |

**Free chat IDs** (docs pricing Free; probed 2026-08-17 with no key):

| ID | Notes |
|----|--------|
| `nemotron-3-ultra-free` | Default first fast/strong |
| `hy3-free` | Failover |
| `nemotron-3.5-lightning-free` | Failover |
| `laguna-s-2.1-free` | May 503 |
| `mimo-v2.5-free` | May 429 |
| `deepseek-v4-flash-free` | May 429 |
| `big-pickle` | Reasoning; on strong failover |

Removed (not on live `/models`): `ling-3.0-*-free`, `longcat-2.0-free`, `north-mini-code-free`.

Paid Zen GPT/Grok use `/v1/responses`; Claude/Qwen use `/v1/messages`. Those need a Zen key. Providence’s default path does **not** use them.

---

## Gemini (thinker only)

| | |
|--|--|
| Docs | [OpenAI-compatible Gemini](https://ai.google.dev/gemini-api/docs/openai) |
| Base | `https://generativelanguage.googleapis.com/v1beta/openai` |
| Auth | `GEMINI_API_KEY` (AI Studio) |
| Models | `gemini-3.5-flash-lite` → `3.1-flash-lite` → `3.6-flash` → `2.5-flash` |

Scout fires three parallel Gemini calls when the key is set. Mid-loop thinker hops run only if the mode dial enables thinker (`deep` / `academic` / `ultra-long`).

Free-tier Gemini may use prompts to improve Google products. Rate limits: [AI Studio](https://aistudio.google.com/rate-limit). Scout is 3 calls — 429s happen; wait and retry.

There is **no** Zen/Groq fallback on the thinker tier.

---

## Optional paid (not default)

These register only when the env key is present, and only if you add them to a tier in `providers.yaml`. Current shipped tiers do **not** put Groq/OpenAI first.

| Provider | Base | Key | Protocol |
|----------|------|-----|----------|
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `openai_chat` |
| OpenAI | `https://api.openai.com/v1` | `OPENAI_API_KEY` | `openai_chat` |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | `openai_chat` |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | `NVIDIA_API_KEY` | `openai_chat` |
| DeepSeek | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` | `openai_chat` |
| Claude | `https://api.anthropic.com` | `ANTHROPIC_API_KEY` | `anthropic_messages` |
| Cohere | `https://api.cohere.com/v2/chat` | `CO_API_KEY` | `cohere_v2_chat` |

---

## Search / extract keys (not LLMs)

| Key | Role |
|-----|------|
| `EXA_API_KEY` | Primary neural search + page text |
| `TAVILY_API_KEY` | Optional search/extract |
| `FIRECRAWL_API_KEY` | Cloud crawl (or self-host on :3002) |
| `NEWSDATA_API_KEY` | Optional newswire |
| GDELT | No key |

---

## Probe

```bash
uv run python main.py doctor
```

Doctor lists live routes and pings the first Zen free model with no key.
