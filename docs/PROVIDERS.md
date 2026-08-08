# LLM providers (final)

**Status:** Final catalog for implementation.  
**Verified:** 2026-08-08 (official docs + live probes).  
**Rule:** Official documentation and live `GET /models` only — never invent model IDs.

Related: [SPEC.md](SPEC.md) · [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Config UX

- **Empty base URL** → OpenCode Zen free open endpoint (`https://opencode.ai/zen/v1`)
- **Empty API key** → no `Authorization` header
- **`+` provider** → any base URL + optional key
- **`+` model** → free-text model id, or import from `GET …/models`

---

## 1. OpenCode Zen (open free endpoints — verified live)

| | |
|--|--|
| **Docs** | [opencode.ai/docs/zen](https://opencode.ai/docs/zen/) |
| **Base URL** | `https://opencode.ai/zen/v1` |
| **Chat** | `POST /chat/completions` (OpenAI-compatible for free OSS routes) |
| **Models list** | `GET https://opencode.ai/zen/v1/models` |
| **Auth** | Free models: **none** (HTTP 200 without key). Paid models: `401 Missing API key` without key |

**Free model IDs** (docs pricing Free; **re-probe before relying**):

| Model ID | Docs | Live no-key probe (2026-08-08 audit) |
|----------|------|--------------------------------------|
| `deepseek-v4-flash-free` | Free | ✅ 200 — **preferred default** |
| `big-pickle` | Free | ✅ 200 — **preferred default** |
| `mimo-v2.5-free` | Free | ✅ 200 |
| `nemotron-3-ultra-free` | Free | ✅ 200 |
| `laguna-s-2.1-free` | Free | ✅ 200 |
| `ling-3.0-tiny-free` / `ling-3.0-flash-free` | Free | (catalog; re-check) |
| `longcat-2.0-free` | Free | (catalog; re-check) |
| `north-mini-code-free` | Free | ⚠️ **401 upstream** at audit time — treat as flaky |

Paid Zen models use other path shapes (`/responses`, `/messages`) and require `OPENCODE_API_KEY` — see Zen endpoints table in their docs.

> **Code status:** the running gateway does **not** yet register OpenCode free without keys. That is **Phase A**. Until then use Groq/OpenAI/OpenRouter keys.

**Go** (subscription): base `https://opencode.ai/zen/go/v1` — needs key for inference; models at `GET …/go/v1/models`.

---

## 2. North Mini Code — what official sources actually say

| Source | What it documents |
|--------|-------------------|
| **[docs.cohere.com](https://docs.cohere.com/docs/models)** | Hosted API models are **Command / Embed / Rerank / Aya / Transcribe** (e.g. `command-a-plus-05-2026`, `command-a-03-2025`, …). **North Mini Code is not listed as a Cohere Platform hosted model ID.** |
| **Cohere Chat API** | `POST https://api.cohere.com/v2/chat` — Bearer token; **not** OpenAI `/v1/chat/completions`. Native **citations** when `documents` are passed. |
| **Hugging Face** | Open weights: `CohereLabs/North-Mini-Code-1.0` (agentic coding model, Apache-2.0). |
| **OpenRouter** | Hosted free: model id **`cohere/north-mini-code:free`** (pricing prompt/completion `0`). |
| **OpenCode Zen** | Hosted free open: model id **`north-mini-code-free`** on zen `/v1/chat/completions` (no key). |

**How we should wire “North Mini Code”:**

1. **Default free path:** OpenCode Zen `north-mini-code-free` (empty URL + empty key).  
2. **Alternate free path:** OpenRouter `cohere/north-mini-code:free` + `OPENROUTER_API_KEY`.  
3. **Official Cohere Platform path:** use **Command** models via `api.cohere.com/v2/chat` (different protocol adapter), not pretend North is on Platform.  
4. **Self-host:** HF weights behind your own OpenAI-compatible URL → add via `+` provider.

---

## 3. DeepSeek — current official models (not chat/reasoner)

Source: [api-docs.deepseek.com](https://api-docs.deepseek.com/) and [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing).

| | |
|--|--|
| **Base URL (OpenAI format)** | `https://api.deepseek.com` |
| **Base URL (Anthropic format)** | `https://api.deepseek.com/anthropic` |
| **Models** | **`deepseek-v4-flash`**, **`deepseek-v4-pro`** only |
| **Auth** | `Authorization: Bearer $DEEPSEEK_API_KEY` |

**Outdated / do not use as current defaults:** `deepseek-chat`, `deepseek-reasoner` (legacy; not what current first-call docs specify).

Thinking mode (docs): `thinking: {"type": "enabled"}` + `reasoning_effort` (e.g. `high`) on chat completions.

---

## 4. NVIDIA NIM (cloud integrate API)

Source: [docs.api.nvidia.com/nim — LLM APIs](https://docs.api.nvidia.com/nim/reference/llm-apis).

| | |
|--|--|
| **URL** | `https://integrate.api.nvidia.com` |
| **Chat** | `POST /v1/chat/completions` → client base **`https://integrate.api.nvidia.com/v1`** |
| **Auth** | API key from [build.nvidia.com](https://build.nvidia.com) as Bearer |
| **Models** | Many; ids are org/name style, e.g. `nvidia/nemotron-3-ultra-550b-a55b`, `deepseek-ai/deepseek-v4-flash`, `openai/gpt-oss-20b`, `meta/llama-3.3-70b-instruct`, … |

**Do not hardcode a single NIM model.** Prefer `GET /v1/models` when available, or user `+` model after viewing build.nvidia.com / docs catalog.

Local NIM containers use their own host (e.g. `http://localhost:8000/v1`) — custom `+` provider.

---

## 5. OpenRouter

Source: [openrouter.ai/docs/quickstart](https://openrouter.ai/docs/quickstart).

| | |
|--|--|
| **Base URL** | `https://openrouter.ai/api/v1` |
| **Chat** | `POST /chat/completions` |
| **Models** | `GET /api/v1/models` — **always prefer live list** |
| **Auth** | `Authorization: Bearer $OPENROUTER_API_KEY` |
| **Optional headers** | `HTTP-Referer`, `X-OpenRouter-Title` |

Examples present live (among many): `cohere/north-mini-code:free`, `xiaomi/mimo-v2.5`, `xiaomi/mimo-v2.5-pro`. Model slugs change; never freeze a stale shortlist as “the” catalog.

---

## 6. OpenAI

Source: OpenAI platform API (chat completions).

| | |
|--|--|
| **Base URL** | `https://api.openai.com/v1` |
| **Chat** | `POST /chat/completions` |
| **Auth** | `Authorization: Bearer $OPENAI_API_KEY` |
| **Models** | From `GET /v1/models` or Console — **do not hardcode outdated ids in product defaults** |

Use live models list / user selection for production defaults.

---

## 7. Claude (Anthropic)

Source: [platform.claude.com API overview](https://platform.claude.com/docs/en/api/getting-started), [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview).

| | |
|--|--|
| **Base URL** | `https://api.anthropic.com` |
| **Chat** | **`POST /v1/messages`** (not OpenAI chat by default) |
| **Auth** | Header **`x-api-key`** *or* `Authorization: Bearer` (WIF); required **`anthropic-version`** (e.g. `2023-06-01`) |
| **Current model ids (docs table)** | `claude-fable-5`, `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5` / `claude-haiku-4-5-20251001` (+ legacy dated ids) |

Requires a **separate protocol adapter** (`anthropic_messages`), not naive openai_chat.

---

## 8. Gemini (Google AI)

Source: [OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).

| | |
|--|--|
| **Base URL** | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| **Chat** | `…/chat/completions` |
| **Auth** | `Authorization: Bearer $GEMINI_API_KEY` (AI Studio key) |
| **Example model in docs** | `gemini-3.6-flash` |

List models: `GET …/openai/models` with the same key. Prefer live list over frozen ids.

### Thinker agent (Gemini free tier)

| | |
|--|--|
| **Role** | Large-context **thinking only** (no tools) for Planner/Critic/structure |
| **Key** | `GEMINI_API_KEY` or `GOOGLE_API_KEY` from [AI Studio](https://aistudio.google.com/apikey) |
| **Preferred** | Free-eligible **Flash** models (long context + speed) — pick current free Flash in AI Studio |
| **Rate limits** | Official: [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) — **RPM · TPM · RPD** per project/model/tier; **view live in [AI Studio rate-limit](https://aistudio.google.com/rate-limit)** (not a single static free table for all models). RPD resets midnight Pacific. Free tier spend-based 10-min limit: **N/A**. |
| **Pricing free** | Free input/output on eligible free-tier models; free tier content **may improve Google products** ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) |
| **Product policy** | Gateway-enforced RPM for `gemini/*`; backoff on 429; call Thinker sparingly (not every node); fallback to OpenCode free / Groq / DeepSeek |

---

## 9. Groq

Source: [OpenAI compatibility](https://console.groq.com/docs/openai), [Models](https://console.groq.com/docs/models).

| | |
|--|--|
| **Base URL** | `https://api.groq.com/openai/v1` |
| **Auth** | `Authorization: Bearer $GROQ_API_KEY` |
| **Models list** | `GET https://api.groq.com/openai/v1/models` |

**Production model ids (docs table, verify live):**

| Model ID | Notes |
|----------|--------|
| `llama-3.1-8b-instant` | Fast |
| `llama-3.3-70b-versatile` | |
| `openai/gpt-oss-20b` | ~1000 t/s class |
| `openai/gpt-oss-120b` | |
| `groq/compound` / `groq/compound-mini` | Agentic systems |

---

## 10. MiMo

| Source | Model id |
|--------|----------|
| OpenCode Zen free | `mimo-v2.5-free` (open, no key) |
| OpenRouter (live) | `xiaomi/mimo-v2.5`, `xiaomi/mimo-v2.5-pro` |

Not a separate “MiMo official OpenAI base” in the same way as DeepSeek docs — treat as **Zen free** and/or **OpenRouter Xiaomi** slugs, refreshed from catalogs.

---

## 11. Official Cohere Platform (Command) — optional first-class adapter

| | |
|--|--|
| **Docs** | [Chat API](https://docs.cohere.com/reference/chat), [Models](https://docs.cohere.com/docs/models) |
| **Endpoint** | `POST https://api.cohere.com/v2/chat` |
| **Auth** | Bearer `CO_API_KEY` / Cohere token |
| **Models** | e.g. `command-a-plus-05-2026`, `command-a-03-2025`, `command-a-reasoning-08-2025`, … |
| **Why it matters for us** | Native **document citations** in chat responses when `documents` is set — strong fit for research grounding |

Protocol: **`cohere_v2_chat`**, not openai_chat.

---

## 12. Protocol matrix (implementation)

| Provider | Protocol | Key empty allowed? |
|----------|----------|--------------------|
| OpenCode Zen free | `openai_chat` | **Yes** |
| NVIDIA NIM integrate | `openai_chat` | No (cloud) |
| OpenRouter | `openai_chat` | No |
| OpenAI | `openai_chat` | No |
| Groq | `openai_chat` | No |
| DeepSeek | `openai_chat` | No |
| Gemini OpenAI-compat | `openai_chat` | No |
| Claude | `anthropic_messages` | No |
| Cohere Platform | `cohere_v2_chat` | No |
| Custom / Ollama | `openai_chat` | Often yes |

---

## 13. Runtime rule

```text
model_id source of truth =
  1) user-added ids via [+]
  2) GET {base}/models when endpoint works
  3) preset seeds only as *examples*, revalidated on doctor/fetch
```

Never ship `deepseek-chat` / `deepseek-reasoner` as current defaults.
