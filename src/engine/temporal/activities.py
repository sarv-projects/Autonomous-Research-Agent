"""
Temporal activities — individual units of work executed by Temporal workers.

Each activity corresponds to a step in the research workflow and can be
retried independently with configurable policies. Includes human-in-the-loop approval management.
"""

from datetime import datetime
import uuid
from typing import Dict, List, Optional
from temporalio import activity

# Import gateway and LLM functions
from src.llm import call_llm
from src.engine.agents.planner import planner
from src.engine.agents.researcher import researcher_gather, researcher_analyze
from src.engine.agents.synthesizer import synthesizer_write, synthesizer_outline
from src.engine.agents.compiler import compiler

# Persistent store for pending human approval requests
_PENDING_APPROVALS: Dict[str, Dict] = {}


def register_approval_request(gate_type: str, data: Dict) -> str:
    """Register a new human approval request in the system."""
    approval_id = f"appr_{uuid.uuid4().hex[:8]}"
    _PENDING_APPROVALS[approval_id] = {
        "approval_id": approval_id,
        "gate_type": gate_type,
        "data": data,
        "status": "pending",
        "requested_at": datetime.utcnow().isoformat(),
        "decision": None,
        "approved": False,
        "comments": "",
    }
    return approval_id


def get_pending_approvals() -> List[Dict]:
    """Retrieve all currently pending approval requests."""
    return [req for req in _PENDING_APPROVALS.values() if req["status"] == "pending"]


def submit_human_approval(approval_id: str, approved: bool, comments: str = "") -> bool:
    """Submit a response for a pending human approval request."""
    if approval_id not in _PENDING_APPROVALS:
        return False
    
    req = _PENDING_APPROVALS[approval_id]
    req["status"] = "resolved"
    req["approved"] = approved
    req["decision"] = "approved" if approved else "rejected"
    req["comments"] = comments
    req["resolved_at"] = datetime.utcnow().isoformat()
    return True


def _full_state(query: str, config: Optional[Dict] = None) -> Dict:
    """Build a complete ResearchState dict (never a partial TypedDict)."""
    from src.state import initial_state
    state = dict(initial_state(query))
    if config:
        # Only merge known-safe keys
        for key in (
            "mode", "autonomy", "quality", "budgets", "mode_flags",
            "max_iterations", "search_queries", "plan", "outline",
            "findings", "claims", "evidence_map",
        ):
            if key in config:
                state[key] = config[key]
        if config.get("max_iterations"):
            state["max_iterations"] = int(config["max_iterations"])
    return state


@activity.defn
async def plan_research_activity(query: str, config: Dict) -> Dict:
    """Activity: Plan the research approach using the Planner agent."""
    state = _full_state(query, config)
    planned_state = planner(state)

    return {
        "topic": planned_state.get("plan", {}).get("topic", query),
        "subtopics": planned_state.get("plan", {}).get("subtopics", []),
        "outline": planned_state.get("outline", []),
        "search_queries": planned_state.get("search_queries", []),
        "findings": planned_state.get("findings", []),
    }


@activity.defn
async def research_subtask_activity(subtask: Dict, config: Dict) -> Dict:
    """Activity: Execute a research subtask using the Researcher agent."""
    query = subtask.get("query") or subtask.get("title") or config.get("query", "")
    state = _full_state(query, config)
    if subtask.get("search_queries"):
        state["search_queries"] = subtask["search_queries"]
    elif query:
        state["search_queries"] = [query]

    gathered = researcher_gather(state)
    analyzed = researcher_analyze(gathered)

    return {
        "findings": analyzed.get("findings", []),
        "sources": [r.get("url") for r in analyzed.get("search_results", []) if r.get("url")],
        "claims": analyzed.get("claims", []),
        "evidence_map": analyzed.get("evidence_map", {}),
    }


@activity.defn
async def synthesize_report_activity(plan: Dict, results: List, config: Dict) -> str:
    """Activity: Synthesize the final report using Synthesizer and Compiler agents."""
    query = plan.get("topic") or config.get("query", "")
    state = _full_state(query, config)
    state["plan"] = plan
    state["outline"] = plan.get("outline", [])

    all_findings: List = []
    all_claims: List = []
    all_evidence: Dict = {}

    for result in results:
        all_findings.extend(result.get("findings", []))
        all_claims.extend(result.get("claims", []))
        all_evidence.update(result.get("evidence_map", {}))

    state["findings"] = all_findings
    state["claims"] = all_claims
    state["evidence_map"] = all_evidence

    outlined = synthesizer_outline(state)
    synthesized = synthesizer_write(outlined)
    compiled = compiler(synthesized)

    return compiled.get("report", "")


@activity.defn
async def human_approval_activity(gate_type: str, data: Dict) -> Dict:
    """
    Activity: Request human approval for workflow gates.

    Polls pending store until resolved or timeout. Default autonomy L1/L3
    auto-approves; L2 waits up to timeout_s for an operator via REST API.
    """
    import asyncio

    approval_id = register_approval_request(gate_type, data)
    autonomy = (data or {}).get("autonomy") or (data or {}).get("config", {}).get("autonomy", "L1")
    timeout_s = float((data or {}).get("timeout_s") or 3600)

    # L1 / L3: auto-approve immediately (unattended)
    if str(autonomy).upper() in ("L1", "L3", ""):
        submit_human_approval(approval_id, True, comments=f"auto-approved under autonomy={autonomy}")
        return {
            "approval_id": approval_id,
            "approved": True,
            "approved_by": f"system_autonomy_{autonomy or 'L1'}",
            "approved_at": datetime.utcnow().isoformat(),
            "comments": f"Auto-approved gate={gate_type}",
        }

    # L2: poll for human response
    deadline = datetime.utcnow().timestamp() + timeout_s
    while datetime.utcnow().timestamp() < deadline:
        req = _PENDING_APPROVALS.get(approval_id)
        if req and req["status"] == "resolved":
            return {
                "approval_id": approval_id,
                "approved": bool(req["approved"]),
                "approved_by": "human_operator",
                "approved_at": req.get("resolved_at", datetime.utcnow().isoformat()),
                "comments": req.get("comments", ""),
            }
        await asyncio.sleep(2.0)

    # Timeout → reject to be safe under L2
    submit_human_approval(approval_id, False, comments="timed out waiting for human")
    return {
        "approval_id": approval_id,
        "approved": False,
        "approved_by": "system_timeout",
        "approved_at": datetime.utcnow().isoformat(),
        "comments": f"Timed out after {timeout_s}s for gate={gate_type}",
    }


@activity.defn
async def gateway_llm_activity(prompt: str, model: str = "fast", system_prompt: str = "") -> str:
    """
    Activity: Gateway LLM call wrapped as Temporal activity.
    """
    system = system_prompt or "You are a research assistant."
    return call_llm(system, prompt, model=model)
