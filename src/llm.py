"""
Groq / multi-provider LLM wrapper routed through the resilient gateway.

The interface is unchanged (``call_llm`` / ``call_llm_strong``) so the existing
LangGraph nodes keep working. Under the hood every call now goes through the
BYOK LLM gateway, gaining:

- multi-provider failover (Groq -> OpenAI -> OpenRouter chain from env)
- circuit breakers per model endpoint
- retries with exponential backoff + full jitter
- per-(tenant, model) rate limiting and concurrency caps
- cost/token accounting + metrics for the dashboard

Env vars (see src/gateway/__init__.py for the full list):
    GROQ_API_KEY / GROQ_API_KEY_2..N / OPENAI_API_KEY... / OPENROUTER_API_KEY...
"""

import os

from dotenv import load_dotenv

from src.gateway import build_gateway_from_env
from src.gateway.router import AllRoutesFailed, QuotaExceeded

load_dotenv()

# Fast model for most tasks, strong model for synthesis.
DEFAULT_MODEL = "gpt-oss-20b"
STRONG_MODEL = "gpt-oss-120b"

_gateway = None


def _get_gateway():
    global _gateway
    if _gateway is None:
        _gateway = build_gateway_from_env()
    return _gateway


def _tier_for(model: str) -> str:
    if model == DEFAULT_MODEL:
        return "fast"
    if model == STRONG_MODEL:
        return "strong"
    return model


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,  # kept for API compatibility; gateway does its own retries
) -> str:
    gw = _get_gateway()
    tier = _tier_for(model)
    if not gw.get_routes(tier):
        # If a custom/unknown model tier has no routes, fall back to "fast".
        tier = "fast"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        result = gw.complete(messages, model=tier)
    except QuotaExceeded as e:
        raise RuntimeError(f"Quota / rate limit exceeded: {e}")
    except AllRoutesFailed as e:
        raise RuntimeError(f"All LLM providers failed: {e}")
    return result.text


def call_llm_strong(system_prompt: str, user_prompt: str) -> str:
    """Use the stronger model tier for synthesis."""
    return call_llm(system_prompt, user_prompt, model=STRONG_MODEL)
