"""Runtime budget enforcement for research runs."""

from __future__ import annotations

import time
from typing import Any


def check_budgets(state: dict) -> tuple[bool, str]:
    """Return (ok, reason). If not ok, research should stop / force complete."""
    budgets = state.get("budgets") or {}
    if not budgets:
        return True, ""

    # Time
    started = float(budgets.get("started_at") or 0)
    max_time = int(budgets.get("max_time_s") or 0)
    if started and max_time > 0:
        elapsed = time.time() - started
        if elapsed > max_time:
            return False, f"Time budget exceeded ({elapsed:.0f}s > {max_time}s)"

    # Cost
    spent = float(budgets.get("spent_usd") or 0)
    max_cost = float(budgets.get("max_cost_usd") or 0)
    if max_cost > 0 and spent >= max_cost:
        return False, f"Cost budget exceeded (${spent:.4f} >= ${max_cost:.2f})"

    # Tool calls
    tool_calls = int(budgets.get("tool_calls") or 0)
    max_tools = int(budgets.get("max_tool_calls") or 0)
    if max_tools > 0 and tool_calls >= max_tools:
        return False, f"Tool-call budget exceeded ({tool_calls} >= {max_tools})"

    return True, ""


def record_tool_calls(state: dict, n: int = 1) -> None:
    budgets = state.setdefault("budgets", {})
    budgets["tool_calls"] = int(budgets.get("tool_calls") or 0) + n


def sync_cost_from_metrics(state: dict) -> None:
    """Best-effort: pull estimated spend from gateway metrics into state budgets."""
    try:
        from src.gateway.metrics import DEFAULT_METRICS
        snap = DEFAULT_METRICS.snapshot()
        total = 0.0
        for _prov, models in (snap.get("per_provider_model") or {}).items():
            for _model, stats in (models or {}).items():
                total += float(stats.get("cost_usd") or 0)
        # Store absolute total; delta accounting is approximate across concurrent runs
        budgets = state.setdefault("budgets", {})
        base = float(budgets.get("_cost_baseline") or 0)
        if "_cost_baseline" not in budgets:
            budgets["_cost_baseline"] = total
            budgets["spent_usd"] = 0.0
        else:
            budgets["spent_usd"] = max(0.0, total - base)
    except Exception:
        pass


def force_complete(state: dict, reason: str) -> dict:
    state["needs_more_research"] = False
    state["status"] = f"Budget stop: {reason}"
    state["gaps"] = list(state.get("gaps") or []) + [f"Budget: {reason}"]
    return state
