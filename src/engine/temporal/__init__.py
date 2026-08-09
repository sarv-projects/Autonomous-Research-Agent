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

from temporalio import workflow

from .workflows import ResearchWorkflow
from .activities import (
    plan_research_activity,
    research_subtask_activity,
    synthesize_report_activity,
)

__all__ = [
    "ResearchWorkflow",
    "plan_research_activity",
    "research_subtask_activity",
    "synthesize_report_activity",
]
