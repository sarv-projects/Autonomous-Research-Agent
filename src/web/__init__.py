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
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml

from src.llm import call_llm, gateway_info, reset_gateway
from src.graph import run_research
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


class ChatResponse(BaseModel):
    response: str
    mode: str
    session_id: str
    cost: float
    tokens: int


class ResearchRequest(BaseModel):
    query: str
    mode: str = "standard"
    autonomy: str = "L1"


class ResearchResponse(BaseModel):
    report: str
    query: str
    mode: str
    iterations: int
    findings: int
    sources: int
    cost: float
    duration_seconds: float


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


# Health check endpoint
@app.get("/api/status")
async def get_status():
    """Health check endpoint displaying system and gateway readiness."""
    info = gateway_info()
    metrics = DEFAULT_METRICS.snapshot()
    return {
        "status": "healthy",
        "version": "0.2.0",
        "gateway": {
            "fast_routes": info.get("fast_routes", 0),
            "strong_routes": info.get("strong_routes", 0),
            "total_routes": len(info.get("routes", [])),
        },
        "metrics": {
            "total_calls": metrics.get("calls", 0),
            "total_tokens": metrics.get("tokens", 0),
            "total_cost_usd": round(metrics.get("cost_usd", 0.0), 6),
        }
    }


# Chat endpoint with Multi-Turn ChatMemory & Cost Metrics
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint supporting multi-turn conversation memory and telemetry."""
    try:
        session_id = request.session_id or "default"
        memory = get_chat_memory(session_id)
        
        # Add user message to session memory
        memory.add("user", request.message)
        
        # Build context from previous conversation turns
        SYSTEM_PROMPT = (
            "You are a helpful, knowledgeable research assistant. "
            "Answer accurately, provide technical depth, and cite sources when possible."
        )
        context_msgs = memory.build_context(SYSTEM_PROMPT)
        
        # Format context for model call
        formatted_context = ""
        for msg in context_msgs[-6:]:
            role = msg.get("role", "user").capitalize()
            formatted_context += f"{role}: {msg.get('content', '')}\n"

        user_prompt = f"Previous Conversation Context:\n{formatted_context}\n\nCurrent Request: {request.message}"

        metrics_before = DEFAULT_METRICS.snapshot()
        response_text = call_llm(SYSTEM_PROMPT, user_prompt, model=request.mode)
        metrics_after = DEFAULT_METRICS.snapshot()

        cost_delta = round(metrics_after.get("cost_usd", 0.0) - metrics_before.get("cost_usd", 0.0), 6)
        tokens_delta = metrics_after.get("tokens", 0) - metrics_before.get("tokens", 0)
        if tokens_delta <= 0:
            tokens_delta = int(len(response_text.split()) * 1.3)

        # Record assistant response in memory
        memory.add("assistant", response_text)

        return ChatResponse(
            response=response_text,
            mode=request.mode,
            session_id=session_id,
            cost=max(0.0, cost_delta),
            tokens=tokens_delta
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Research endpoint
@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Deep multi-agent research endpoint."""
    start = time.time()
    try:
        metrics_before = DEFAULT_METRICS.snapshot()
        result = run_research(request.query, mode=request.mode)
        elapsed = time.time() - start
        metrics_after = DEFAULT_METRICS.snapshot()

        report = result.get("report", "")
        findings = len(result.get("findings", []))
        sources = len(result.get("evidence_map", {}))
        iterations = result.get("iteration", 0)

        cost_delta = round(metrics_after.get("cost_usd", 0.0) - metrics_before.get("cost_usd", 0.0), 6)

        return ResearchResponse(
            report=report,
            query=request.query,
            mode=request.mode,
            iterations=iterations,
            findings=findings,
            sources=sources,
            cost=max(0.0, cost_delta),
            duration_seconds=round(elapsed, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            "providers": "/api/providers",
            "history": "/api/history",
            "vault_search": "/api/vault/search",
            "approvals": "/api/approvals",
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Autonomous Research Agent API server...")
    print("Docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
