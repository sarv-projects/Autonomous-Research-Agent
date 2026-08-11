"""
Multi-provider LLM wrapper routed through the resilient gateway.

The interface is unchanged (``call_llm`` / ``call_llm_strong``) so the existing
LangGraph nodes keep working. Under the hood every call goes through the
BYOK LLM gateway with:

- Multi-provider failover (paid keys → Zen free default)
- Circuit breakers per model endpoint
- Retries with exponential backoff + full jitter
- Per-(tenant, model) rate limiting and concurrency caps
- Cost/token accounting + metrics for the dashboard

Provider priority:
  1. Paid providers from env (Groq > OpenAI > OpenRouter) when keys present
  2. OpenCode Zen free (mimo-v2.5-free, always available, no key needed)
"""

import os

from dotenv import load_dotenv

from src.gateway import build_gateway_from_env
from src.gateway.router import AllRoutesFailed, QuotaExceeded

load_dotenv()

# Fast model for most tasks, strong model for synthesis.
DEFAULT_MODEL = "fast"
STRONG_MODEL = "strong"

_gateway = None


def _get_gateway():
    global _gateway
    if _gateway is None:
        _gateway = build_gateway_from_env()
    return _gateway


def reset_gateway() -> None:
    """Reset the gateway singleton (useful for testing)."""
    global _gateway
    _gateway = None


def gateway_info() -> dict:
    """Return info about currently available providers and models."""
    gw = _get_gateway()
    info = {
        "fast_routes": len(gw.get_routes("fast")),
        "strong_routes": len(gw.get_routes("strong")),
        "thinker_routes": len(gw.get_routes("thinker")),
        "routes": [],
    }
    for tier in ("fast", "strong", "thinker"):
        for route in gw.get_routes(tier):
            info["routes"].append({
                "tier": tier,
                "provider": route.provider.name,
                "model": route.model,
                "has_key": bool(getattr(route.provider, "api_keys", [])),
            })
    return info


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,  # kept for API compatibility; gateway does its own retries
    max_tokens: int | None = None,
) -> str:
    gw = _get_gateway()
    tier = model if model in ("fast", "strong", "thinker") else DEFAULT_MODEL
    if not gw.get_routes(tier):
        # If the tier has no routes, fall back to "fast".
        if tier != "fast" and gw.get_routes("fast"):
            tier = "fast"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        result = gw.complete(messages, model=tier, max_tokens=max_tokens)
    except QuotaExceeded as e:
        raise RuntimeError(f"Quota / rate limit exceeded: {e}")
    except AllRoutesFailed as e:
        raise RuntimeError(f"All LLM providers failed: {e}")
    return result.text


def call_llm_strong(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int | None = None,
) -> str:
    """Use the stronger model tier for synthesis."""
    return call_llm(system_prompt, user_prompt, model=STRONG_MODEL, max_tokens=max_tokens)


def call_llm_stream(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
):
    """Streaming LLM call — yields text chunks via generator.

    Uses the gateway's streaming transport. Falls back to non-streaming
    if the provider doesn't support streaming.
    """
    gw = _get_gateway()
    tier = model if model in ("fast", "strong", "thinker") else DEFAULT_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        yield from gw.complete_stream(messages, model=tier)
    except (QuotaExceeded, AllRoutesFailed) as e:
        raise RuntimeError(f"LLM streaming failed: {e}")
