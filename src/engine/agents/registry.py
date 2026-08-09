"""
Agent registry — maps agent names to their graph node functions.

Each agent is a callable that takes ResearchState and returns ResearchState.
The registry allows the graph to be built declaratively from agent names.
"""

from __future__ import annotations

from typing import Callable

from src.state import ResearchState

AgentFunc = Callable[[ResearchState], ResearchState]

_registry: dict[str, AgentFunc] = {}


def register(name: str) -> Callable:
    """Decorator to register an agent node function."""
    def wrapper(fn: AgentFunc) -> AgentFunc:
        _registry[name] = fn
        return fn
    return wrapper


def get_agent(name: str) -> AgentFunc:
    """Get a registered agent by name."""
    return _registry[name]


def get_all() -> dict[str, AgentFunc]:
    """Return a copy of the full registry."""
    return dict(_registry)
