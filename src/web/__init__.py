"""
Web API server for the Autonomous Research Agent.

Provides REST API endpoints for frontend, CLI, and integration tools:
  - GET  /api/status - System health and gateway routes
  - POST /api/chat - Multi-turn chat endpoint with memory and token/cost metrics
  - POST /api/research - Autonomous multi-agent research endpoint
  - GET  /api/providers - List configured provider catalog slots
  - POST /api/providers - Dynamically register new providers
  - GET  /api/history - Past search and research history
  - GET  /api/vault/search - Query persistent research vault
  - GET  /api/approvals - List pending human approval requests
  - POST /api/approvals/{approval_id}/respond - Respond to pending workflow approval
"""

import time
import os
import json
import threading
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import yaml

from src.llm import call_llm, call_llm_stream, gateway_info, reset_gateway
from src.graph import run_research, create_research_plan
from src.memory import get_history as get_search_history
from src.providers.catalog import load_catalog
from src.rag.chat_memory import get_chat_memory
from src.rag.vault import Vault
from src.gateway.metrics import DEFAULT_METRICS
from src.engine.temporal.activities import get_pending_approvals, submit_human_approval

# Create FastAPI app
app = FastAPI(
    title="Autonomous Research Agent API",
    description="REST API for the Autonomous Research Agent engine",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    message: str
    mode: str = "fast"
    session_id: Optional[str] = "default"
    max_tokens: Optional[int] = None
    stream: bool = False
    escalate: bool = True  # allow auto-escalation to research


class ChatResponse(BaseModel):
    response: str
    mode: str
    session_id: str
    cost: float
    tokens: int
    escalated: bool = False


class ResearchRequest(BaseModel):
    query: str
    mode: str = "standard"
    autonomy: str = "L1"
    background: bool = False  # if true, return immediately and run async
    plan_first: bool = False  # L1 optional: return editable plan before research
    plan_id: Optional[str] = None
    approved_plan: Optional[dict] = None
    clarifications: Optional[dict] = None  # question -> answer
    skip_clarify: bool = False


class ResearchResponse(BaseModel):
    report: str
    query: str
    mode: str
    iterations: int
    findings: int
    sources: int
    cost: float
    duration_seconds: float


class PlanCreateRequest(BaseModel):
    query: str
    mode: str = "standard"
    autonomy: str = "L1"
    clarifications: Optional[dict] = None


class PlanUpdateRequest(BaseModel):
    plan: Optional[dict] = None
    outline: Optional[list] = None
    search_queries: Optional[list] = None
    clarifications: Optional[dict] = None


class PlanRunRequest(BaseModel):
    background: bool = True
    clarifications: Optional[dict] = None


class ClarifyRequest(BaseModel):
    query: str


class ProviderRequest(BaseModel):
    name: str
    display_name: Optional[str] = None
    base_url: str
    api_key: Optional[str] = ""
    protocol: str = "openai_chat"
    models: List[str]


class ProviderResponse(BaseModel):
    name: str
    base_url: str
    has_auth: bool
    models: List[str]


class ApprovalResponseRequest(BaseModel):
    approved: bool
    comments: Optional[str] = ""


def _metrics_totals(snap: dict) -> dict:
    """Aggregate totals from MetricsRegistry.snapshot() (correct keys)."""
    total_tokens = 0
    total_cost = 0.0
    for _prov, models in (snap.get("per_provider_model") or {}).items():
        for _model, stats in (models or {}).items():
            total_tokens += int(stats.get("prompt_tokens") or 0) + int(
                stats.get("completion_tokens") or 0
            )
            total_cost += float(stats.get("cost_usd") or 0)
    return {
        "total_calls": int(snap.get("total_calls") or 0),
        "total_errors": int(snap.get("total_errors") or 0),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "uptime_s": snap.get("uptime_s", 0),
    }


# Health check endpoint
@app.get("/api/status")
async def get_status():
    """Health check endpoint displaying system and gateway readiness."""
    info = gateway_info()
    metrics = _metrics_totals(DEFAULT_METRICS.snapshot())
    return {
        "status": "healthy",
        "version": "0.2.0",
        "gateway": {
            "fast_routes": info.get("fast_routes", 0),
            "strong_routes": info.get("strong_routes", 0),
            "total_routes": len(info.get("routes", [])),
        },
        "metrics": metrics,
    }


def _chat_should_escalate(text: str) -> bool:
    t = text.lower().strip()
    if len(t.split()) < 8:
        return False
    triggers = (
        "research", "deep dive", "comprehensive", "compare ", " vs ",
        "versus", "literature review", "survey of", "write a report",
        "investigate", "analyze in depth", "pros and cons",
    )
    return any(x in t for x in triggers)


def _build_chat_prompt(memory, system_prompt: str) -> str:
    context_msgs = memory.build_context(system_prompt)
    history_lines = []
    for msg in context_msgs:
        role = msg.get("role", "user")
        if role == "system":
            continue
        history_lines.append(f"{role.upper()}: {msg.get('content', '')}")
    return (
        "Conversation so far:\n"
        + "\n".join(history_lines[-16:])
        + "\n\nRespond to the latest user message."
    )


# Chat endpoint with Multi-Turn ChatMemory & Cost Metrics
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint supporting multi-turn memory, streaming, and research escalation."""
    try:
        session_id = request.session_id or "default"
        memory = get_chat_memory(session_id)
        memory.add("user", request.message)

        SYSTEM_PROMPT = (
            "You are a helpful, knowledgeable research assistant. "
            "Answer accurately, provide technical depth, and cite sources when possible."
        )

        # Auto-escalate deep research intents
        if request.escalate and _chat_should_escalate(request.message):
            def _bg_research() -> None:
                try:
                    run_research(request.message, mode="standard", autonomy="L1")
                except Exception as exc:
                    print(f"  [chat escalate] research failed: {exc}")

            threading.Thread(target=_bg_research, daemon=True).start()
            msg = (
                f"Escalated to deep research for: **{request.message[:120]}**\n\n"
                "Research is running in the background. Poll `/api/research/progress` "
                "or open the Research tab when complete."
            )
            memory.add("assistant", msg)
            return ChatResponse(
                response=msg,
                mode="research",
                session_id=session_id,
                cost=0.0,
                tokens=0,
                escalated=True,
            )

        user_prompt = _build_chat_prompt(memory, SYSTEM_PROMPT)
        tier = request.mode if request.mode in ("fast", "strong", "thinker") else "fast"

        # Streaming SSE
        if request.stream:
            def event_gen():
                full = []
                try:
                    for chunk in call_llm_stream(SYSTEM_PROMPT, user_prompt, model=tier):
                        full.append(chunk)
                        yield f"data: {json.dumps({'type': 'token', 'text': chunk})}\n\n"
                    text = "".join(full)
                    memory.add("assistant", text)
                    yield f"data: {json.dumps({'type': 'done', 'text': text})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            return StreamingResponse(event_gen(), media_type="text/event-stream")

        before = _metrics_totals(DEFAULT_METRICS.snapshot())
        response_text = call_llm(SYSTEM_PROMPT, user_prompt, model=tier, max_retries=3)
        after = _metrics_totals(DEFAULT_METRICS.snapshot())

        cost_delta = round(after["total_cost_usd"] - before["total_cost_usd"], 6)
        tokens_delta = after["total_tokens"] - before["total_tokens"]
        if tokens_delta <= 0:
            tokens_delta = int(len(response_text.split()) * 1.3)

        memory.add("assistant", response_text)

        return ChatResponse(
            response=response_text,
            mode=request.mode,
            session_id=session_id,
            cost=max(0.0, cost_delta),
            tokens=tokens_delta,
            escalated=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Research endpoint
@app.post("/api/research")
async def research(request: ResearchRequest):
    """Deep multi-agent research endpoint (sync or background).

    background=True (default for UI): creates a job, runs async, returns job_id.
    plan_first / L2: returns editable plan (plan_id) before gather.
    Poll /api/research/progress or /api/jobs/{job_id}.
    """
    start = time.time()
    try:
        autonomy = request.autonomy or "L1"

        # Editable plan path (L1 optional via plan_first, L2 required)
        if request.plan_first or (
            autonomy.upper() == "L2"
            and not request.approved_plan
            and not request.background
        ):
            payload = create_research_plan(
                request.query,
                mode=request.mode,
                autonomy=autonomy,
                clarifications=request.clarifications,
            )
            return {
                "status": payload.get("status", "draft"),
                "query": request.query,
                "mode": request.mode,
                "plan_id": payload.get("plan_id"),
                "plan": payload.get("plan"),
                "outline": payload.get("outline"),
                "search_queries": payload.get("search_queries"),
                "clarifying_questions": payload.get("clarifying_questions"),
                "needs_clarification": payload.get("needs_clarification"),
                "message": "Review/edit the plan, then POST /api/research/plans/{plan_id}/run",
            }

        if request.background:
            result = run_research(
                request.query,
                mode=request.mode,
                autonomy=autonomy,
                background=True,
                approved_plan=request.approved_plan,
                plan_id=request.plan_id or "",
                clarifications=request.clarifications,
                skip_clarify=request.skip_clarify,
            )
            job_id = result.get("job_id", "")
            return {
                "status": "started",
                "query": request.query,
                "mode": request.mode,
                "job_id": job_id,
                "plan_id": request.plan_id,
                "message": (
                    f"Research started (job_id={job_id}). "
                    "Poll /api/research/progress or /api/jobs/{job_id}"
                ),
            }

        before = _metrics_totals(DEFAULT_METRICS.snapshot())
        result = run_research(
            request.query,
            mode=request.mode,
            autonomy=autonomy,
            approved_plan=request.approved_plan,
            plan_id=request.plan_id or "",
            clarifications=request.clarifications,
            skip_clarify=request.skip_clarify,
        )
        elapsed = time.time() - start
        after = _metrics_totals(DEFAULT_METRICS.snapshot())

        # Plan-only intermediate response
        if result.get("plan_id") and not result.get("report"):
            return {
                "status": result.get("status", "draft"),
                "query": request.query,
                "mode": request.mode,
                "plan_id": result.get("plan_id"),
                "plan": result.get("plan"),
                "outline": result.get("outline"),
                "search_queries": result.get("search_queries"),
                "clarifying_questions": result.get("clarifying_questions"),
                "message": "Plan ready for review",
            }

        report = result.get("report", "")
        findings = len(result.get("findings", []))
        sources = len(result.get("evidence_map", {}))
        iterations = result.get("iteration", 0)
        cost_delta = round(after["total_cost_usd"] - before["total_cost_usd"], 6)

        return ResearchResponse(
            report=report,
            query=request.query,
            mode=request.mode,
            iterations=iterations,
            findings=findings,
            sources=sources,
            cost=max(0.0, cost_delta),
            duration_seconds=round(elapsed, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/clarify")
async def research_clarify(request: ClarifyRequest):
    """Generate clarifying questions for an ambiguous query (P2.1)."""
    from src.engine.clarify import generate_clarifying_questions
    return generate_clarifying_questions(request.query)


@app.post("/api/research/plans")
async def create_plan(request: PlanCreateRequest):
    """Create an editable research plan (does not start gather)."""
    try:
        return create_research_plan(
            request.query,
            mode=request.mode,
            autonomy=request.autonomy or "L1",
            clarifications=request.clarifications,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/research/plans")
async def list_plans(limit: int = 20):
    from src.engine.plan_store import get_plans
    return {"plans": get_plans().list_recent(limit=limit)}


@app.get("/api/research/plans/{plan_id}")
async def get_plan(plan_id: str):
    from src.engine.plan_store import get_plans
    p = get_plans().get(plan_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    return p.to_dict()


@app.put("/api/research/plans/{plan_id}")
async def update_plan(plan_id: str, request: PlanUpdateRequest):
    """Edit outline / queries / clarifications on a draft plan."""
    from src.engine.plan_store import get_plans
    store = get_plans()
    p = store.get(plan_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    fields = {}
    if request.plan is not None:
        fields["plan"] = request.plan
    if request.outline is not None:
        fields["outline"] = request.outline
    if request.search_queries is not None:
        fields["search_queries"] = request.search_queries
    if request.clarifications is not None:
        fields["clarifications"] = request.clarifications
        fields["needs_clarification"] = False
    fields["status"] = "draft" if p.status == "awaiting_clarification" else p.status
    updated = store.update(plan_id, **fields)
    return updated.to_dict() if updated else {"error": "update failed"}


@app.post("/api/research/plans/{plan_id}/run")
async def run_plan(plan_id: str, request: PlanRunRequest = PlanRunRequest()):
    """Approve plan (optionally after edits) and start research."""
    from src.engine.plan_store import get_plans
    store = get_plans()
    p = store.get(plan_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    clarifications = request.clarifications or p.clarifications or None
    # If still needs clarification and L2, re-generate plan with answers
    if p.needs_clarification and clarifications:
        payload = create_research_plan(
            p.query, mode=p.mode, autonomy=p.autonomy, clarifications=clarifications
        )
        # Keep same flow with new plan_id
        plan_id = payload["plan_id"]
        p = store.get(plan_id)
        if not p:
            raise HTTPException(status_code=500, detail="Failed to rebuild plan")

    approved = {
        "plan": p.plan,
        "outline": p.outline,
        "search_queries": p.search_queries,
    }
    store.update(plan_id, status="approved")

    result = run_research(
        p.query,
        mode=p.mode,
        autonomy=p.autonomy,
        background=request.background,
        approved_plan=approved,
        plan_id=plan_id,
        clarifications=clarifications,
        skip_clarify=True,
    )
    job_id = result.get("job_id", "")
    if job_id:
        store.update(plan_id, job_id=job_id, status="running")
    return {
        "status": "started" if request.background else "complete",
        "plan_id": plan_id,
        "job_id": job_id,
        "query": p.query,
        "mode": p.mode,
        "report": result.get("report", "") if not request.background else "",
        "message": f"Research started from plan {plan_id}",
    }


# List providers endpoint
@app.get("/api/providers", response_model=List[ProviderResponse])
async def list_providers():
    """List all configured provider catalog slots."""
    try:
        catalog = load_catalog()
        providers = []
        for name, slot in catalog.providers.items():
            providers.append(ProviderResponse(
                name=slot.display_name or name,
                base_url=slot.effective_base_url,
                has_auth=slot.has_auth,
                models=slot.models
            ))
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dynamic Provider Registration endpoint
@app.post("/api/providers")
async def add_provider(request: ProviderRequest):
    """Dynamically register a new LLM provider and write to config/providers.yaml."""
    try:
        config_path = os.path.join("config", "providers.yaml")
        raw_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                raw_config = yaml.safe_load(f) or {}

        if "providers" not in raw_config:
            raw_config["providers"] = {}

        provider_key = request.name.lower().replace(" ", "_")
        raw_config["providers"][provider_key] = {
            "name": request.display_name or request.name,
            "base_url": request.base_url,
            "api_key_env": f"{provider_key.upper()}_API_KEY",
            "models": request.models
        }

        # If API key provided, update environment variable
        if request.api_key:
            os.environ[f"{provider_key.upper()}_API_KEY"] = request.api_key

        os.makedirs("config", exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(raw_config, f, default_flow_style=False)

        # Reset gateway singleton so new provider routes are dynamically registered
        reset_gateway()

        return {
            "status": "success",
            "message": f"Provider '{request.name}' registered successfully.",
            "provider": provider_key,
            "models": request.models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register provider: {e}")


# History endpoint
@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get recent research search history."""
    try:
        return get_search_history(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vault search endpoint
@app.get("/api/vault/search")
async def search_vault(query: str, limit: int = 10):
    """Search the research vault for cached source documents and findings."""
    try:
        vault = Vault()
        results = vault.search(query, k=limit)
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "limit": limit
        }
    except Exception as e:
        # Fallback empty response if vault unavailable
        return {"query": query, "results": [], "count": 0, "limit": limit, "warning": str(e)}


# Pending Approvals Endpoint (Human-in-the-Loop)
@app.get("/api/approvals")
async def list_approvals():
    """List pending workflow approval requests."""
    try:
        approvals = get_pending_approvals()
        return {"approvals": approvals, "count": len(approvals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approvals/{approval_id}/respond")
async def respond_approval(approval_id: str, request: ApprovalResponseRequest):
    """Submit a response to a pending human approval request."""
    try:
        success = submit_human_approval(
            approval_id=approval_id,
            approved=request.approved,
            comments=request.comments or ""
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Approval request '{approval_id}' not found or already processed.")
        return {"status": "success", "approval_id": approval_id, "approved": request.approved}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Settings persistence (workspace-level JSON) ─────────────────────
class SettingsModel(BaseModel):
    mode: str = "standard"
    autonomy: str = "L1"
    max_cost: float = 5.0
    max_iterations: int = 3
    default_model: str = "opencode_free/laguna-s-2.1-free"


def _settings_path() -> str:
    return os.path.join("data", "workspace_settings.json")


@app.get("/api/settings")
async def get_settings():
    """Load workspace research settings."""
    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}  # yaml handles JSON too poorly; use json
        except Exception:
            data = {}
        # Prefer json
        try:
            import json
            with open(path, "r") as f:
                data = json.load(f)
        except Exception:
            pass
        return data
    return SettingsModel().model_dump()


@app.post("/api/settings")
async def save_settings(settings: SettingsModel):
    """Persist workspace research settings to data/workspace_settings.json."""
    import json
    os.makedirs("data", exist_ok=True)
    path = _settings_path()
    payload = settings.model_dump()
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return {"status": "success", "settings": payload}


@app.get("/api/research/progress")
async def research_progress():
    """Snapshot of current research progress (for polling UIs)."""
    from src.engine.progress import get_progress
    return get_progress().snapshot()


@app.get("/api/research/progress/stream")
async def research_progress_stream():
    """SSE stream of research progress until finished."""
    from src.engine.progress import get_progress

    def event_gen():
        progress = get_progress()
        last = ""
        while True:
            snap = progress.snapshot()
            payload = json.dumps(snap)
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            if snap.get("finished"):
                break
            time.sleep(0.8)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/api/jobs")
async def list_jobs(limit: int = 20):
    """List recent research jobs (async job state)."""
    from src.engine.jobs import get_jobs
    return {"jobs": get_jobs().list_recent(limit=limit)}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a single research job by id (for leave-and-return)."""
    from src.engine.jobs import get_jobs
    job = get_jobs().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job.to_dict()


@app.get("/api/reports")
async def list_reports(limit: int = 30):
    """List generated research reports on disk (markdown + html)."""
    reports_dir = os.getenv("REPORTS_DIR", "reports")
    if not os.path.isdir(reports_dir):
        return {"reports": [], "count": 0}
    items = []
    for name in sorted(os.listdir(reports_dir), reverse=True):
        if not (name.endswith(".md") or name.endswith(".html")):
            continue
        path = os.path.join(reports_dir, name)
        try:
            st = os.stat(path)
            items.append({
                "name": name,
                "path": os.path.abspath(path),
                "format": "html" if name.endswith(".html") else "markdown",
                "size_bytes": st.st_size,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            })
        except OSError:
            continue
        if len(items) >= limit:
            break
    return {"reports": items, "count": len(items)}


@app.get("/api/reports/{name}")
async def get_report(name: str):
    """Fetch a report file by basename (markdown preferred for UI)."""
    # Prevent path traversal
    safe = os.path.basename(name)
    reports_dir = os.getenv("REPORTS_DIR", "reports")
    path = os.path.join(reports_dir, safe)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {
        "name": safe,
        "path": os.path.abspath(path),
        "format": "html" if safe.endswith(".html") else "markdown",
        "content": content[:200000],
    }


@app.get("/api/modes")
async def list_modes():
    """List configured research modes and quality dials."""
    from src.engine.modes import load_modes
    registry = load_modes()
    modes = []
    for name, m in registry.modes.items():
        modes.append({
            "name": name,
            "description": m.description,
            "max_iterations": m.budgets.max_iterations,
            "max_cost_usd": m.budgets.max_cost_usd,
            "quality_dial": m.quality_dial,
            "requires_temporal": m.requires_temporal,
            "structured_output": m.structured_output,
            "academic_bias": m.academic_bias,
            "recency_bias": m.recency_bias,
        })
    return {"modes": modes, "default": registry.default_mode}


@app.get("/api/models")
async def list_models(discover: bool = True, probe: bool = False, provider: Optional[str] = None):
    """
    Model picker data.

    - discover=true: also fetch remote /v1/models when keys exist
    - probe=true: live-test models (slow). If provider= set, only that provider.
      If provider omitted and probe=true, only probes OpenCode Zen free (safe/fast).
    """
    from src.providers.models_catalog import (
        list_catalog_models,
        group_for_picker,
        probe_zen_free,
        probe_provider,
        probe_model,
    )

    rows = list_catalog_models(discover_remote=discover)
    probes_map: dict = {}

    if probe:
        if provider:
            results = probe_provider(provider, max_models=15)
        else:
            # Default: only probe free Zen (always safe, no key)
            results = probe_zen_free()
        for r in results:
            probes_map[f"{r['provider']}/{r['model']}"] = r

    groups = group_for_picker(rows, probes_map)
    return {
        "groups": groups,
        "probes": list(probes_map.values()),
        "default_provider": "opencode_free",
        "default_model": "laguna-s-2.1-free",
        "note": "OpenCode Zen free models require no API key. Set GROQ_API_KEY / NVIDIA_API_KEY / etc. for paid providers.",
    }


@app.post("/api/models/probe")
async def probe_models_endpoint(body: dict):
    """
    Probe specific models.

    Body:
      { "provider": "opencode_free", "model": "mimo-v2.5-free" }
      or { "provider": "groq" }  # probe all configured models for provider
      or { "zen_free": true }    # probe all Zen free
    """
    from src.providers.models_catalog import probe_model, probe_provider, probe_zen_free

    if body.get("zen_free"):
        return {"results": probe_zen_free()}
    provider = body.get("provider")
    model = body.get("model")
    if provider and model:
        return {"results": [probe_model(provider, model)]}
    if provider:
        return {"results": probe_provider(provider)}
    raise HTTPException(status_code=400, detail="Provide zen_free, or provider, or provider+model")


# Root endpoint
@app.get("/")
async def root():
    """Root API discovery endpoint."""
    return {
        "name": "Autonomous Research Agent API",
        "version": "0.2.0",
        "docs": "/docs",
        "endpoints": {
            "status": "/api/status",
            "chat": "/api/chat",
            "research": "/api/research",
            "research_progress": "/api/research/progress",
            "research_progress_stream": "/api/research/progress/stream",
            "jobs": "/api/jobs",
            "job": "/api/jobs/{job_id}",
            "research_plans": "/api/research/plans",
            "research_clarify": "/api/research/clarify",
            "providers": "/api/providers",
            "history": "/api/history",
            "vault_search": "/api/vault/search",
            "approvals": "/api/approvals",
            "settings": "/api/settings",
            "reports": "/api/reports",
            "modes": "/api/modes",
            "models": "/api/models",
            "models_probe": "/api/models/probe",
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Autonomous Research Agent API server...")
    print("Docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
