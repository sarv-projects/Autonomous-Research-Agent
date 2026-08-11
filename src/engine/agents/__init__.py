"""
Multi-agent implementations for the research engine.

Importing this package registers all agents in the registry.
"""

from .registry import register, get_agent, get_all
from .planner import planner
from .researcher import researcher_gather, researcher_analyze
from .thinker import (
    thinker_query_scout,
    thinker_plan_refine,
    thinker_contradiction_check,
    thinker_search_strategy,
)
from .adversary import devil_advocate_gather, claim_adjudicator
from .triangulator import triangulator
from .critic import critic
from .synthesizer import synthesizer_outline, synthesizer_write
from .compiler import compiler

__all__ = [
    "register", "get_agent", "get_all",
    "planner",
    "researcher_gather", "researcher_analyze",
    "thinker_query_scout",
    "thinker_plan_refine", "thinker_contradiction_check", "thinker_search_strategy",
    "devil_advocate_gather", "claim_adjudicator",
    "triangulator",
    "critic",
    "synthesizer_outline", "synthesizer_write",
    "compiler",
]
