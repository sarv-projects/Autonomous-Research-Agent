"""
OpenAI-compatible provider client (stdlib only).

Groq, OpenAI, OpenRouter, Together, Azure (with OpenAI-compatible endpoint),
local vLLM/Ollama servers, etc. all expose the ``/chat/completions`` REST shape.
This tiny client talks to any of them over HTTPS using only ``urllib`` so the
gateway needs zero extra dependencies. Streaming is intentionally left for a
future iteration (the router currently returns the full completion); the class
is structured so a streaming transport can slot in.

Raises:
    ProviderHTTPError     — JSON error body with an HTTP status
    ProviderTimeoutError  — request exceeded timeout
    ProviderConnectionError — network-level failure (DNS/TLS/connection refused)
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List

DEFAULT_TIMEOUT = 60.0

# Per-model pricing in USD per 1M tokens for cost accounting. Tune as needed.
# (input, output) pairs.
PRICING: Dict[str, tuple] = {
    # Groq production ids often use openai/ prefix; keep bare + prefixed aliases.
    "gpt-oss-20b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "gpt-oss-120b": (0.30, 1.20),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant": (0.05, 0.08),
    "deepseek-v4-flash": (0.14, 0.28),
    "deepseek-v4-pro": (0.435, 0.87),
    "*default": (0.50, 1.50),
}


class ProviderHTTPError(Exception):
    def __init__(self, status: int, message: str, retriable: bool) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.retriable = retriable


class ProviderTimeoutError(Exception):
    pass


class ProviderConnectionError(Exception):
    pass


@dataclass
class ProviderResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    latency_s: float = 0.0


def retriable_status(status: int) -> bool:
    """Which upstream statuses should trigger retry/failover (vs. client bugs)."""
    return status in (408, 429, 500, 502, 503, 504)


class OpenAICompatibleProvider:
    def __init__(self, name: str, base_url: str, api_key: str = "") -> None:
        self.name = name
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        self.base_url = base_url
        self.api_keys = [api_key] if api_key else []

    def _url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> ProviderResult:
        key = api_key or (self.api_keys[0] if self.api_keys else "")
        payload: Dict = {"model": model, "messages": messages, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url(),
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            msg = ""
            try:
                msg = json.loads(e.read().decode("utf-8", "ignore")).get("error", {}).get(
                    "message", str(e)
                )
            except Exception:
                msg = str(e)
            raise ProviderHTTPError(e.code, msg, retriable_status(e.code))
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            if isinstance(e, (socket.timeout, TimeoutError)) or (
                isinstance(e, urllib.error.URLError) and isinstance(e.reason, (socket.timeout, TimeoutError))
            ):
                raise ProviderTimeoutError(f"{self.name} timed out: {e}")
            raise ProviderConnectionError(f"{self.name} connection error: {e}")

        latency = time.time() - start
        try:
            data = json.loads(raw.decode("utf-8"))
            text = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})
            return ProviderResult(
                text=text,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                model=data.get("model", model),
                latency_s=latency,
            )
        except (KeyError, ValueError, IndexError) as e:
            raise ProviderConnectionError(f"{self.name} bad response: {e}")
