"""
Resilient BYOK LLM Gateway — built from scratch, stdlib-only.

Layers:
  keys.py      BYOK: virtual keys (hashed), tenants, budgets, provider-key
               pools with TTL rotation + grace period, optional AES-GCM at rest
  circuit.py   Circuit breakers (CLOSED/OPEN/HALF-OPEN) per route
  ratelimit.py Token-bucket RPM/TPM per (tenant, model) + concurrency cap
  providers.py OpenAI-compatible REST adapters (Groq/OpenAI/OpenRouter/...)
  router.py    Gateway orchestrator: failover chain, retry+jitter, cost, metrics
  metrics.py   Telemetry: calls, errors, latency, tokens, cost, events

``build_gateway_from_env()`` reads environment variables so the existing app
picks up the whole stack with zero code changes:

    GATEWAY_MASTER_KEY           optional master key (encrypts provider secrets)
    GROQ_API_KEY[,_2.._N]        provider key pool (rotation/load-balancing pool)
    OPENAI_API_KEY[,_2.._N]
    OPENROUTER_API_KEY[,_2.._N]
    GATEWAY_MAX_ATTEMPTS         retries per route (default 3)
    GATEWAY_RETRY_BASE_S         backoff base (default 0.5)
    GATEWAY_RETRY_CAP_S          backoff cap (default 8)
    GATEWAY_DEFAULT_RPM          per (tenant, model) requests/min (default 60)
    GATEWAY_MAX_PARALLEL         concurrency cap (default 20)
    GATEWAY_CIRCUIT_THRESHOLD    breaker failures before opening (default 5)
    GATEWAY_CIRCUIT_COOLDOWN_S   breaker cooldown (default 30)
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from .circuit import CircuitRegistry
from .keys import KeyManager
from .metrics import DEFAULT_METRICS
from .providers import OpenAICompatibleProvider
from .ratelimit import RateLimiter
from .router import Gateway, Route


def _env_keys(prefix: str) -> list:
    """Collect GROQ_API_KEY, GROQ_API_KEY_2, ... into an ordered pool."""
    keys = []
    val = os.getenv(prefix)
    if val:
        keys.append(val)
    i = 2
    while True:
        v = os.getenv(f"{prefix}_{i}")
        if not v:
            break
        keys.append(v)
        i += 1
    return keys


def _provider(name: str, key_env: str, base_url_env: str, default_base: str) -> Optional[OpenAICompatibleProvider]:
    keys = _env_keys(key_env)
    if not keys:
        return None
    base = os.getenv(base_url_env, default_base)
    p = OpenAICompatibleProvider(name, base)
    p.api_keys = keys
    return p


def build_gateway_from_env(
    fast_models: Optional[list] = None,
    strong_models: Optional[list] = None,
    clave_circuit_ok: bool = True,
) -> Gateway:
    """
    Build a fully wired Gateway from environment variables.

    Route priority order = order of providers listed. A provider is only
    registered for a model if it has at least one API key configured, so a
    single ``GROQ_API_KEY`` keeps working exactly like before — but now with
    circuit breakers, rate limiting, retries with jitter, cost tracking, etc.
    """
    metrics = DEFAULT_METRICS
    km = KeyManager()
    rl = RateLimiter(
        default_rpm=int(os.getenv("GATEWAY_DEFAULT_RPM", "60")),
        default_tpm=int(os.getenv("GATEWAY_DEFAULT_TPM", "120000")),
        max_parallel=int(os.getenv("GATEWAY_MAX_PARALLEL", "20")),
    )
    circuits = CircuitRegistry(
        failure_threshold=int(os.getenv("GATEWAY_CIRCUIT_THRESHOLD", "5")),
        cooldown_s=float(os.getenv("GATEWAY_CIRCUIT_COOLDOWN_S", "30")),
        half_open_max=int(os.getenv("GATEWAY_CIRCUIT_HALF_OPEN", "2")),
        on_state_change=lambda route, state: metrics.record_circuit_state(route, state),
    )
    gw = Gateway(
        key_manager=km,
        metrics=metrics,
        ratelimiter=rl,
        circuits=circuits,
        max_attempts=int(os.getenv("GATEWAY_MAX_ATTEMPTS", "3")),
        retry_base_s=float(os.getenv("GATEWAY_RETRY_BASE_S", "0.5")),
        retry_cap_s=float(os.getenv("GATEWAY_RETRY_CAP_S", "8")),
    )

    providers = [
        _provider("groq", "GROQ_API_KEY", "GROQ_BASE_URL", "https://api.groq.com/openai"),
        _provider("openai", "OPENAI_API_KEY", "OPENAI_BASE_URL", "https://api.openai.com"),
        _provider("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "https://openrouter.ai/api"),
    ]
    providers = [p for p in providers if p is not None]
    if not providers:
        return gw

    default_fast = [("groq", "gpt-oss-20b"), ("openai", "gpt-4o-mini")]
    default_strong = [("groq", "gpt-oss-120b"), ("openai", "gpt-4o-mini")]

    fast = fast_models or default_fast
    strong = strong_models or default_strong

    def _register_chain(tier: str, plan: list) -> None:
        for i, (prov_name, model) in enumerate(plan):
            prov = next((p for p in providers if p.name == prov_name), None)
            if prov is None:
                continue
            route_name = f"{prov.name}/{model}"
            gw.register(Route(provider=prov, model=model, tier=tier,
                              priority=i + 1, name=route_name))

    _register_chain("fast", [c for c in default_fast] if not fast else fast)
    _register_chain("strong", [c for c in default_strong] if not strong else strong)
    return gw