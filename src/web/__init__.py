"""
Web API server for the Autonomous Research Agent.

This provides a REST API for the research agent, which can be used by
a frontend (web UI, CLI, or other tools). The web UI itself (React/Next.js)
can be implemented separately and consume this API.

Endpoints:
  - GET /api/status - Health check
  - POST /api/chat - Chat endpoint
  - POST /api/research - Research endpoint
  - GET /api/providers - List providers
  - POST /api/providers - Add provider
  - GET /api/history - Research history
  - GET /api/vault/search - Search vault
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.llm import call_llm, gateway_info
from src.graph import run_research
from src.memory import get_history
from src.providers.catalog import load_catalog

# Create FastAPI app
app = FastAPI(
    title="Autonomous Research Agent API",
    description="REST API for the Autonomous Research Agent",
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
    mode: str = "chat"
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    mode: str
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
    base_url: str
    api_key: str
    protocol: str = "openai_chat"
    models: List[str]


class ProviderResponse(BaseModel):
    name: str
    base_url: str
    has_auth: bool
    models: List[str]


# Health check endpoint
@app.get("/api/status")
async def get_status():
    """Health check endpoint."""
    info = gateway_info()
    return {
        "status": "healthy",
        "version": "0.2.0",
        "gateway": {
            "fast_routes": info.get("fast_routes", 0),
            "strong_routes": info.get("strong_routes", 0),
            "total_routes": info.get("routes", 0),
        }
    }


# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for multi-turn conversations."""
    try:
        # TODO: Integrate with chat memory for multi-turn
        response = call_llm(
            "You are a helpful research assistant. Answer accurately and cite sources when possible.",
            request.message,
            tier=request.mode
        )
        
        # TODO: Calculate actual cost and tokens from gateway
        return ChatResponse(
            response=response.content,
            mode=request.mode,
            cost=0.0,  # TODO: get from gateway metrics
            tokens=len(response.content)  # Approximate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Research endpoint
@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Research endpoint for deep research queries."""
    import time
    
    start = time.time()
    
    try:
        # Run research using the graph
        result = run_research(request.query, mode=request.mode)
        elapsed = time.time() - start
        
        # Extract results
        report = result.get("report", "")
        findings = len(result.get("findings", []))
        sources = len(result.get("sources", []))
        iterations = result.get("iteration", 0)
        
        # TODO: Calculate actual cost from gateway metrics
        cost = 0.0
        
        return ResearchResponse(
            report=report,
            query=request.query,
            mode=request.mode,
            iterations=iterations,
            findings=findings,
            sources=sources,
            cost=cost,
            duration_seconds=elapsed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Providers endpoints
@app.get("/api/providers", response_model=List[ProviderResponse])
async def list_providers():
    """List all configured providers."""
    try:
        catalog = load_catalog()
        providers = []
        
        for name, slot in catalog.providers.items():
            providers.append(ProviderResponse(
                name=slot.display_name,
                base_url=slot.effective_base_url,
                has_auth=slot.has_auth,
                models=slot.models
            ))
        
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/providers")
async def add_provider(request: ProviderRequest):
    """Add a new provider (runtime configuration)."""
    # TODO: Implement dynamic provider registration
    # This would require updating the catalog and re-loading the gateway
    raise HTTPException(
        status_code=501,
        detail="Dynamic provider registration not yet implemented. Use config/providers.yaml"
    )


# History endpoint
@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get research history."""
    try:
        history = get_history(limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vault search endpoint
@app.get("/api/vault/search")
async def search_vault(query: str, limit: int = 10):
    """Search the vault for similar past research."""
    # TODO: Implement vault search
    return {"query": query, "results": [], "limit": limit}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
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
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Autonomous Research Agent API server...")
    print("Docs available at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
