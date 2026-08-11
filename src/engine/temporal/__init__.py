"""
Temporal integration — durable execution for 24h+ research runs.

This module provides Temporal.io workflow definitions and activity workers
for the research graph, enabling:
- Crash recovery and workflow resumption
- 24h+ execution with checkpoints
- Human-in-the-loop pause/approval
- Distributed execution across workers

Architecture:
  LangGraph Research Graph → Temporal Workflow → Temporal Activities → Gateway
"""

from .workflows import ResearchWorkflow, HumanInLoopWorkflow
from .activities import (
    plan_research_activity,
    research_subtask_activity,
    synthesize_report_activity,
    human_approval_activity,
)
from .client import try_run_temporal_research, temporal_configured

__all__ = [
    "ResearchWorkflow",
    "HumanInLoopWorkflow",
    "plan_research_activity",
    "research_subtask_activity",
    "synthesize_report_activity",
    "human_approval_activity",
    "try_run_temporal_research",
    "temporal_configured",
]
