# LLM Gateway & ops dashboard (built)

**Status:** Implemented in tree.  
**Code:** `src/gateway/`, `src/dashboard/`

This document supersedes the gateway sections of the older production architecture draft.

---

## 1. Purpose

Every LLM call routes through an in-process **resilient gateway** (stdlib-only):

```
request → (optional BYOK) → budget → rate limit → concurrency
  → circuit check → retry + full jitter → provider failover
  → cost charge → metrics
```

Modeled on LiteLLM / Portkey patterns without requiring those processes.

---

## 2. Modules

| File | Role |
|------|------|
| `keys.py` | Virtual keys (`xa_…`) SHA-256 only; tenants; USD + token budgets; provider key pools + TTL rotation; optional AES-GCM |
| `circuit.py` | CLOSED → OPEN → HALF-OPEN per route; retriable failures only |
| `ratelimit.py` | Token-bucket RPM/TPM per (tenant, model) + global concurrency |
| `providers.py` | OpenAI-compatible HTTP client (`urllib`) |
| `router.py` | Orchestrator: failover, backoff, charge, metrics |
| `metrics.py` | Calls, errors, latency, tokens, cost, event log, Prometheus text |
| `__init__.py` | `build_gateway_from_env()` |

`src/llm.py` exposes `call_llm` / `call_llm_strong` → gateway tiers `fast` / `strong`.

---

## 3. Failure taxonomy

| Class | Examples | Action |
|-------|----------|--------|
| Retriable | 429, 408, 5xx, timeout | Retry + jitter; may open circuit |
| Non-retriable | 400, 401, 403, 404, 422 | Failover; **no** circuit trip |

---

## 4. Current env wiring (today)

Hardcoded env providers: Groq → OpenAI → OpenRouter if keys present.

**Spec target (next):** config-driven slots — empty URL = OpenCode free; optional keys; see [PROVIDERS.md](PROVIDERS.md). Implementation roadmap Phase A.

Env knobs:

```
GATEWAY_MAX_ATTEMPTS
GATEWAY_RETRY_BASE_S
GATEWAY_RETRY_CAP_S
GATEWAY_DEFAULT_RPM / TPM
GATEWAY_MAX_PARALLEL
GATEWAY_CIRCUIT_THRESHOLD
GATEWAY_CIRCUIT_COOLDOWN_S
GATEWAY_MASTER_KEY
```

---

## 5. Dashboard

```bash
uv run python -m src.dashboard --port 8080
```

| Endpoint | Purpose |
|----------|---------|
| `/` | SPA metrics UI |
| `/api/status` | JSON snapshot |
| `/api/events` | SSE event stream |
| `/metrics` | Prometheus scrape |

---

## 6. Tests

```bash
uv run python test_gateway.py   # offline unit tests
```

---

## 7. Security model (gateway)

1. No committed secrets (`.env` gitignored)  
2. Virtual keys hashed at rest  
3. Optional `GATEWAY_MASTER_KEY` for provider secret encryption  
4. Budget kill-switch  
5. Circuit fast-fail on dead upstream  
6. Event log for audit/billing  

---

## 8. Temporal integration (Phase C3)

The gateway integrates with Temporal.io for workflow-level durability and resilience.

### Gateway + Temporal Pattern

```
LangGraph Workflow (Temporal)
    ↓
Temporal Activity (LLM call)
    ↓
Gateway (resilience, metrics)
    ↓
Provider API
```

### Integration Points

| Component | Temporal Role |
|-----------|--------------|
| Gateway activities | Temporal activities with retry policies |
| Circuit breaker state | Persists to Temporal workflow history |
| Metrics | Exposed to Temporal workflow metrics |
| Failover | Handled by gateway, transparent to Temporal |

### Temporal Activity Wrapper

```python
# src/gateway/temporal.py

from temporalio import activity

@activity.defn
async def call_llm_activity(
    prompt: str,
    model: str,
    tier: str = "fast"
) -> str:
    """Gateway LLM call as Temporal activity."""
    
    from src.llm import call_llm
    
    # Gateway handles resilience, metrics, failover
    result = await call_llm(
        prompt=prompt,
        model=model,
        tier=tier
    )
    
    return result.content
```

### Activity Configuration

```python
# Temporal activity options for gateway calls
activity_options = {
    "start_to_close_timeout": timedelta(minutes=5),
    "retry_policy": {
        "max_attempts": 3,
        "initial_interval": "1s",
        "max_interval": "60s",
        "non_retryable_error_types": [
            "ValidationError",
            "AuthenticationError"
        ]
    }
}
```

### Benefits

1. **Workflow-level resilience** — Research runs survive crashes and restarts
2. **Automatic retries** — Temporal retries failed activities with backoff
3. **State persistence** — Gateway state preserved across workflow checkpoints
4. **Observability** — Combined gateway metrics + Temporal workflow history
5. **Distributed execution** — Scale gateway calls across multiple workers

### Monitoring

Gateway metrics are exposed through:
- Dashboard at `/metrics` (Prometheus)
- Temporal workflow execution history
- Temporal workflow metrics API

See [ARCHITECTURE.md §8](ARCHITECTURE.md#8-temporal-integration-new---durable-execution) for Temporal architecture details.

---

## 9. Deferred gateway platform work

- HTTP/sidecar standalone gateway
- OIDC, multi-worker Redis ownership
- Semantic cache, canary routing

See [ROADMAP.md](ROADMAP.md) deferred list.
