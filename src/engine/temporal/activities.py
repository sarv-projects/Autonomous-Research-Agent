"""
Temporal activities — individual units of work executed by Temporal workers.

Each activity corresponds to a step in the research workflow and can be
retried independently with configurable policies.
"""

from datetime import timedelta
from typing import Dict, List

from temporalio import activity

# Import gateway and LLM functions
from src.llm import call_llm
from src.state import ResearchState
from src.engine.agents.planner import planner
from src.engine.agents.researcher import researcher
from src.engine.agents.synthesizer import synthesizer
from src.engine.agents.compiler import compiler


@activity.defn
async def plan_research_activity(query: str, config: Dict) -> Dict:
    """
    Activity: Plan the research approach using the Planner agent.
    
    Args:
        query: The research topic/question
        config: Configuration including mode, budget, autonomy level
        
    Returns:
        Dict with plan including subtasks, outline, and budgets
    """
    # Create a ResearchState for the planner
    state = ResearchState(query=query)
    state.update(config)
    
    # Call the Planner agent
    planned_state = planner(state)
    
    # Return plan as dict
    return {
        "topic": planned_state.get("plan", {}).get("topic", query),
        "subtopics": planned_state.get("plan", {}).get("subtopics", []),
        "outline": planned_state.get("outline", []),
        "search_queries": planned_state.get("search_queries", []),
        "findings": planned_state.get("findings", []),
    }


@activity.defn
async def research_subtask_activity(subtask: Dict, config: Dict) -> Dict:
    """
    Activity: Execute a research subtask using the Researcher agent.
    
    Args:
        subtask: A single research subtask with query and context
        config: Configuration
        
    Returns:
        Dict with research results including findings and sources
    """
    # Create a ResearchState for the researcher
    query = subtask.get("query", "")
    state = ResearchState(query=query)
    state.update(config)
    state.update(subtask)
    
    # Call the Researcher agent
    researched_state = researcher(state)
    
    # Return results as dict
    return {
        "findings": researched_state.get("findings", []),
        "sources": researched_state.get("sources", []),
        "claims": researched_state.get("claims", []),
        "evidence_map": researched_state.get("evidence_map", {}),
    }


@activity.defn
async def synthesize_report_activity(plan: Dict, results: List, config: Dict) -> str:
    """
    Activity: Synthesize the final report using Synthesizer and Compiler agents.
    
    Args:
        plan: The research plan with outline
        results: List of research results from subtasks
        config: Configuration
        
    Returns:
        The final research report as markdown
    """
    # Create a ResearchState for synthesis
    query = plan.get("topic", "")
    state = ResearchState(query=query)
    state.update(config)
    state["plan"] = plan
    state["outline"] = plan.get("outline", [])
    
    # Merge results from all subtasks
    all_findings = []
    all_sources = []
    all_claims = []
    all_evidence = {}
    
    for result in results:
        all_findings.extend(result.get("findings", []))
        all_sources.extend(result.get("sources", []))
        all_claims.extend(result.get("claims", []))
        all_evidence.update(result.get("evidence_map", {}))
    
    state["findings"] = all_findings
    state["sources"] = all_sources
    state["claims"] = all_claims
    state["evidence_map"] = all_evidence
    
    # Call Synthesizer agent
    synthesized_state = synthesizer(state)
    
    # Call Compiler agent for final formatting and export
    compiled_state = compiler(synthesized_state)
    
    # Return the compiled report
    return compiled_state.get("report", "")


@activity.defn
async def human_approval_activity(gate_type: str, data: Dict) -> Dict:
    """
    Activity: Request human approval for workflow gates.
    
    This activity implements human-in-the-loop by:
    1. Saving approval request to a persistent store
    2. Waiting for human to approve via API/CLI
    3. Resuming when approval received
    
    Args:
        gate_type: Type of gate ("plan", "budget", "export")
        data: Data requiring approval
        
    Returns:
        Dict with approval decision and metadata
    """
    # For now, auto-approve (TODO: implement actual human approval mechanism)
    # In production, this would:
    # 1. Write approval request to database
    # 2. Set workflow to "waiting" state
    # 3. Wait for external signal via API
    # 4. Resume when approval received
    
    return {
        "approved": True,
        "approved_by": "auto",
        "approved_at": "pending",
        "comments": "Auto-approved (TODO: implement human approval UI)"
    }


@activity.defn
async def gateway_llm_activity(prompt: str, model: str, tier: str = "fast") -> str:
    """
    Activity: Gateway LLM call wrapped as Temporal activity.
    
    This provides resilience and retry policies for all LLM calls within workflows.
    
    Args:
        prompt: The prompt to send to the LLM
        model: The model to use
        tier: The tier (fast/strong/thinker)
        
    Returns:
        The LLM response content
    """
    # Gateway handles resilience, metrics, failover
    result = await call_llm(
        prompt,
        model=model,
        tier=tier
    )
    return result.content
