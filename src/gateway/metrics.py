"""
Metrics & observability for the LLM gateway.

Production-grade telemetry without any external dependencies:
- per (provider, model) call counters and error counters
- latency ring buffer + histogram buckets
- token accounting (prompt/completion) and estimated USD cost
- circuit breaker state snapshot per route
- rate limiter admissions / denials
- event log ring buffer (for the dashboard / debugging)

Exports:
- ``MetricsRegistry`` in-process singleton you can query
- ``to_prometheus()`` for Prometheus scraping
- ``to_json()`` for the web dashboard
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Tuple

# Latency histogram buckets in seconds.
HISTOGRAM_BUCKETS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0]


class _EventLog:
    """Thread-safe bounded event log (ring buffer)."""

    def __init__(self, capacity: int = 1000) -> None:
        self._q: Deque[Dict[str, Any]] = deque(maxlen=capacity)

    def append(self, event: Dict[str, Any]) -> None:
        self._q.append(event)

    def recent(self, n: int) -> List[Dict[str, Any]]:
        return list(self._q)[-n:]


class MetricsRegistry:
    """Aggregated runtime metrics for the gateway. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._calls: Dict[Tuple[str, str], int] = defaultdict(int)          # (provider, model) -> count
        self._errors: Dict[Tuple[str, str], int] = defaultdict(int)
        self._latency: Deque[float] = deque(maxlen=2000)
        self._buckets: Dict[Tuple[str, str], List[int]] = defaultdict(
            lambda: [0] * len(HISTOGRAM_BUCKETS)
        )
        self._tokens: Dict[Tuple[str, str], List[int]] = defaultdict(
            lambda: [0, 0]
        )  # (provider, model) -> [prompt_tokens, completion_tokens]
        self._cost: Dict[Tuple[str, str], float] = defaultdict(float)
        self._circuits: Dict[str, Dict[str, Any]] = {}
        self._ratelimit = {"admitted": 0, "denied": 0}
        self._events = _EventLog()
        self._started = time.time()

    # ---- call recording -------------------------------------------------
    def record_success(
        self,
        provider: str,
        model: str,
        latency_s: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        tenant: str = "default",
    ) -> None:
        with self._lock:
            key = (provider, model)
            self._calls[key] += 1
            self._latency.append(latency_s)
            self._bucketize(key, latency_s)
            self._tokens[key][0] += prompt_tokens
            self._tokens[key][1] += completion_tokens
            self._cost[key] += cost_usd
            self._events.append(
                {
                    "ts": time.time(),
                    "type": "call",
                    "provider": provider,
                    "model": model,
                    "ok": True,
                    "latency_s": round(latency_s, 4),
                    "tokens": prompt_tokens + completion_tokens,
                    "cost_usd": round(cost_usd, 6),
                    "tenant": tenant,
                }
            )

    def record_error(
        self,
        provider: str,
        model: str,
        error_type: str,
        message: str = "",
        tenant: str = "default",
    ) -> None:
        with self._lock:
            key = (provider, model)
            self._errors[key] += 1
            self._events.append(
                {
                    "ts": time.time(),
                    "type": "error",
                    "provider": provider,
                    "model": model,
                    "ok": False,
                    "error_type": error_type,
                    "message": message[:200],
                    "tenant": tenant,
                }
            )

    def record_circuit_state(self, route: str, state: str) -> None:
        with self._lock:
            self._circuits[route] = {
                "state": state,
                "ts": time.time(),
            }
            self._events.append(
                {"ts": time.time(), "type": "circuit", "route": route, "state": state}
            )

    def record_ratelimit(self, admitted: bool, tenant: str = "default", model: str = "") -> None:
        with self._lock:
            if admitted:
                self._ratelimit["admitted"] += 1
            else:
                self._ratelimit["denied"] += 1
            self._events.append(
                {
                    "ts": time.time(),
                    "type": "ratelimit",
                    "admitted": admitted,
                    "tenant": tenant,
                    "model": model,
                }
            )

    def log_event(self, kind: str, **fields: Any) -> None:
        with self._lock:
            self._events.append({"ts": time.time(), "type": kind, **fields})

    # ---- helpers --------------------------------------------------------
    def _bucketize(self, key: Tuple[str, str], latency_s: float) -> None:
        for i, upper in enumerate(HISTOGRAM_BUCKETS):
            if latency_s <= upper:
                self._buckets[key][i] += 1
                return
        self._buckets[key][-1] += 1

    def uptime_s(self) -> float:
        return time.time() - self._started

    def total_calls(self) -> int:
        with self._lock:
            return sum(self._calls.values())

    def total_errors(self) -> int:
        with self._lock:
            return sum(self._errors.values())
    def snapshot(self) -> Dict[str, Any]:
        """JSON-safe snapshot of everything the dashboard needs."""
        with self._lock:
            per_model: Dict[str, Any] = {}
            for (provider, model), count in sorted(self._calls.items()):
                if provider not in per_model:
                    per_model[provider] = {}
                tokens = self._tokens[(provider, model)]
                latency = self._avg_latency()
                per_model[provider][model] = {
                    "calls": count,
                    "errors": self._errors[(provider, model)],
                    "prompt_tokens": tokens[0],
                    "completion_tokens": tokens[1],
                    "cost_usd": round(self._cost[(provider, model)], 6),
                    "error_rate": round(self._errors[(provider, model)] / count, 4) if count else 0.0,
                    "avg_latency_s": round(latency, 3),
                }
            return {
                "uptime_s": round(self.uptime_s(), 1),
                "total_calls": self.total_calls(),
                "total_errors": self.total_errors(),
                "per_provider_model": per_model,
                "circuits": dict(self._circuits),
                "ratelimit": dict(self._ratelimit),
                "event_log": self._events.recent(200),
                "histogram_buckets": HISTOGRAM_BUCKETS,
            }

    def _avg_latency(self) -> float:
        if not self._latency:
            return 0.0
        return sum(self._latency) / len(self._latency)

    def to_json(self) -> str:
        return json.dumps(self.snapshot(), default=str)

    def to_prometheus(self) -> str:
        """Expose plain-text Prometheus format for scraping in prod."""
        with self._lock:
            lines = [
                "# HELP gateway_llm_calls_total Total LLM calls.",
                "# TYPE gateway_llm_calls_total counter",
            ]
            for (provider, model), count in sorted(self._calls.items()):
                lines.append(
                    f'gateway_llm_calls_total{{provider="{provider}",model="{model}"}} {count}'
                )
            lines.append("# HELP gateway_llm_errors_total Total LLM errors by provider/model.")
            lines.append("# TYPE gateway_llm_errors_total counter")
            for (provider, model), count in sorted(self._errors.items()):
                lines.append(
                    f'gateway_llm_errors_total{{provider="{provider}",model="{model}"}} {count}'
                )
            lines.append("# HELP gateway_llm_cost_usd Accumulated estimated USD cost.")
            lines.append("# TYPE gateway_llm_cost_usd counter")
            for (provider, model), cost in sorted(self._cost.items()):
                lines.append(
                    f'gateway_llm_cost_usd{{provider="{provider}",model="{model}"}} {cost:.6f}'
                )
            return "\n".join(lines) + "\n"


# Process-wide default registry. Callers may create their own.
DEFAULT_METRICS = MetricsRegistry()
