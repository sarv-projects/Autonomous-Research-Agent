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


def _zen_free_provider() -> OpenAICompatibleProvider:
    """Create the OpenCode Zen free provider (no API key required)."""
    p = OpenAICompatibleProvider("opencode_free", "https://opencode.ai/zen/v1")
    p.api_keys = []  # empty = no Authorization header
    return p


def build_gateway_from_env(
    fast_models: Optional[list] = None,
    strong_models: Optional[list] = None,
    clave_circuit_ok: bool = True,
    use_catalog: bool = True,
) -> Gateway:
    """
    Build a fully wired Gateway from environment variables or catalog config.

    Route priority: paid providers (if keys present) → Zen free (always available).
    A single ``GROQ_API_KEY`` keeps working exactly like before — just now with
    Zen free as fallback when no paid keys are configured.

    Args:
        use_catalog: If True, load from config/providers.yaml. If False, use env vars only.
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

    # Zen free is always available (no key)
    zen = _zen_free_provider()

    # Try to load from catalog if enabled
    if use_catalog:
        try:
            from src.providers.catalog import load_catalog
            catalog = load_catalog()
            if catalog.providers:
                # Map provider_name → OpenAICompatibleProvider
                catalog_providers: dict = {}
                for provider_name, slot in catalog.providers.items():
                    if provider_name == "opencode_free" or not slot.base_url:
                        # Reuse the shared zen free provider
                        prov = zen
                        if slot._all_keys if hasattr(slot, "_all_keys") else []:
                            prov.api_keys = getattr(slot, "_all_keys", []) or prov.api_keys
                    else:
                        protocol = getattr(slot, "protocol", "openai_chat") or "openai_chat"
                        prov = OpenAICompatibleProvider(
                            slot.name,
                            slot.effective_base_url,
                            protocol=protocol,
                        )
                        prov.api_keys = (
                            slot._all_keys
                            if hasattr(slot, "_all_keys")
                            else ([slot.api_key] if slot.api_key else [])
                        )
                    catalog_providers[provider_name] = prov

                # Always ensure zen free is in the map
                catalog_providers.setdefault("opencode_free", zen)

                registered = 0
                for tier_name, tier_config in catalog.tiers.items():
                    for route in tier_config.routes:
                        prov = catalog_providers.get(route.provider_name)
                        if prov is None:
                            continue
                        route_name = f"{prov.name}/{route.model}"
                        gw.register(
                            Route(
                                provider=prov,
                                model=route.model,
                                tier=tier_name,
                                priority=route.priority,
                                name=route_name,
                            )
                        )
                        registered += 1

                # Ensure free fallback routes if a tier is empty
                # Thinker is Gemini-only — do not backfill it with Zen.
                for tier_name, free_model in (
                    ("fast", "nemotron-3-ultra-free"),
                    ("strong", "nemotron-3-ultra-free"),
                ):
                    if not gw.get_routes(tier_name):
                        gw.register(
                            Route(
                                provider=zen,
                                model=free_model,
                                tier=tier_name,
                                priority=99,
                                name=f"{zen.name}/{free_model}",
                            )
                        )
                        registered += 1

                if registered:
                    return gw
        except Exception:
            # Fall back to env-based config if catalog fails
            pass

    # ── Fallback: Environment-based configuration ──
    paid_providers = [
        # Docs: https://console.groq.com/docs/openai — base_url ends with /openai/v1
        _provider("groq", "GROQ_API_KEY", "GROQ_BASE_URL", "https://api.groq.com/openai"),
        _provider("openai", "OPENAI_API_KEY", "OPENAI_BASE_URL", "https://api.openai.com"),
        _provider("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "https://openrouter.ai/api"),
        _provider("gemini", "GEMINI_API_KEY", "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"),
        _provider("deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    ]
    paid_providers = [p for p in paid_providers if p is not None]

    # Zen free FIRST for every tier — paid keys are last-resort only
    default_fast = [
        ("opencode_free", "nemotron-3-ultra-free"),
        ("opencode_free", "hy3-free"),
        ("opencode_free", "nemotron-3.5-lightning-free"),
        ("opencode_free", "laguna-s-2.1-free"),
        ("opencode_free", "mimo-v2.5-free"),
        ("opencode_free", "deepseek-v4-flash-free"),
        ("groq", "llama-3.1-8b-instant"),
        ("openai", "gpt-4o-mini"),
    ]
    default_strong = [
        ("opencode_free", "nemotron-3-ultra-free"),
        ("opencode_free", "hy3-free"),
        ("opencode_free", "deepseek-v4-flash-free"),
        ("opencode_free", "big-pickle"),
        ("opencode_free", "nemotron-3.5-lightning-free"),
        ("groq", "openai/gpt-oss-120b"),
        ("openai", "gpt-4o-mini"),
    ]
    default_thinker = [
        ("gemini", "gemini-3.5-flash-lite"),
        ("gemini", "gemini-3.1-flash-lite"),
        ("gemini", "gemini-3.6-flash"),
        ("gemini", "gemini-2.5-flash"),
    ]

    fast = fast_models or default_fast
    strong = strong_models or default_strong
    thinker = default_thinker

    def _register_chain(tier: str, plan: list) -> None:
        for i, (prov_name, model) in enumerate(plan):
            prov = next((p for p in [*paid_providers, zen] if p.name == prov_name), None)
            if prov is None:
                continue
            route_name = f"{prov.name}/{model}"
            gw.register(Route(provider=prov, model=model, tier=tier,
                              priority=i + 1, name=route_name))

    _register_chain("fast", list(fast))
    _register_chain("strong", list(strong))
    _register_chain("thinker", list(thinker))

    return gw
