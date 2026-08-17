# Gateway and ops dashboard

Every LLM call goes through `src/gateway/` (stdlib HTTP, no LiteLLM process).

```
request → budget → rate limit → concurrency
  → circuit → retry + jitter → next route in the tier
  → cost + metrics
```

Tiers come from `config/providers.yaml`. Workhorse = Zen free. Thinker = Gemini only. See [PROVIDERS.md](PROVIDERS.md).

| Module | Role |
|--------|------|
| `router.py` | Failover, retries, charge |
| `providers.py` | OpenAI / Anthropic / Cohere HTTP |
| `circuit.py` | CLOSED / OPEN / HALF-OPEN |
| `ratelimit.py` | RPM / TPM / parallelism |
| `metrics.py` | Calls, tokens, cost, Prometheus |
| `keys.py` | Optional BYOK / tenant budgets |

`src/llm.py`: `call_llm(..., model="fast"|"strong"|"thinker"|"task")`. `task` aliases `fast`.

Retriable (429, 408, 5xx, timeout) → retry, may open circuit.  
Non-retriable (400, 401, 403, 404) → next route, no circuit trip.

Env knobs: `GATEWAY_MAX_ATTEMPTS`, `GATEWAY_RETRY_*`, `GATEWAY_DEFAULT_RPM`, `GATEWAY_DEFAULT_TPM`, `GATEWAY_MAX_PARALLEL`, `GATEWAY_CIRCUIT_*`, `GATEWAY_MASTER_KEY`.

## Dashboard

```bash
uv run python -m src.dashboard --port 8080
```

| Path | What |
|------|------|
| `/` | Metrics UI |
| `/api/status` | JSON + tool-bus `search_cache` |
| `/api/events` | SSE |
| `/metrics` | Prometheus |

```bash
uv run python test_gateway.py
```

Not included: standalone HTTP sidecar, Redis multi-worker ownership, wrapping the A4 graph as Temporal activities.
