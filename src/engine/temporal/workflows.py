"""
Temporal workflows for durable research execution.

Defines the main research workflow that wraps the LangGraph research graph
with Temporal's durable execution capabilities.
"""

from datetime import timedelta
from typing import Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities import (
    plan_research_activity,
    research_subtask_activity,
    synthesize_report_activity,
    human_approval_activity,
)


@workflow.defn
class ResearchWorkflow:
    """Temporal workflow for autonomous research with durable execution."""
    
    @workflow.run
    async def run(self, query: str, config: Dict) -> str:
        """
        Execute the full research workflow with durable execution.
        
        Args:
            query: The research topic/question
            config: Configuration including mode, budget, autonomy level
            
        Returns:
            The final research report as markdown
        """
        # Step 1: Plan research
        plan = await workflow.execute_activity(
            plan_research_activity,
            args=[query, config],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                max_attempts=3,
                initial_interval=timedelta(seconds=1),
                max_interval=timedelta(seconds=60),
            ),
        )
        
        # Step 2: Execute research subtasks in parallel
        subtasks = plan.get("subtasks", [])
        results = []
        
        for subtask in subtasks:
            result = await workflow.execute_activity(
                research_subtask_activity,
                args=[subtask, config],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    max_interval=timedelta(seconds=120),
                ),
            )
            results.append(result)
        
        # Step 3: Synthesize final report
        report = await workflow.execute_activity(
            synthesize_report_activity,
            args=[plan, results, config],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(
                max_attempts=2,
                initial_interval=timedelta(seconds=5),
                max_interval=timedelta(seconds=30),
            ),
        )
        
        return report


@workflow.defn
class HumanInLoopWorkflow:
    """Workflow with human-in-the-loop approval gates."""
    
    @workflow.run
    async def run(self, query: str, config: Dict) -> str:
        """
        Execute research with human approval gates.
        
        This workflow pauses at key points for human approval:
        - After initial plan
        - Before expensive operations
        - Before final export
        """
        # Step 1: Plan and wait for approval
        plan = await workflow.execute_activity(
            plan_research_activity,
            args=[query, config],
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        # Human approval gate
        approval = await workflow.execute_activity(
            human_approval_activity,
            args=["plan", plan],
            start_to_close_timeout=timedelta(hours=24),  # Give human 24h to approve
        )
        
        if not approval.get("approved", False):
            return "Research cancelled by user"
        
        # Step 2: Execute research
        subtasks = plan.get("subtasks", [])
        results = []
        
        for subtask in subtasks:
            # Check budget before expensive operations
            if subtask.get("expensive", False):
                budget_approval = await workflow.execute_activity(
                    human_approval_activity,
                    args=["budget", subtask],
                    start_to_close_timeout=timedelta(hours=1),
                )
                if not budget_approval.get("approved", False):
                    continue
            
            result = await workflow.execute_activity(
                research_subtask_activity,
                args=[subtask, config],
                start_to_close_timeout=timedelta(minutes=30),
            )
            results.append(result)
        
        # Step 3: Synthesize and wait for final approval
        report = await workflow.execute_activity(
            synthesize_report_activity,
            args=[plan, results, config],
            start_to_close_timeout=timedelta(minutes=15),
        )
        
        # Final approval gate
        final_approval = await workflow.execute_activity(
            human_approval_activity,
            args=["export", {"report": report}],
            start_to_close_timeout=timedelta(hours=24),
        )
        
        if not final_approval.get("approved", False):
            return "Report export cancelled by user"
        
        return report
