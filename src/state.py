from typing import TypedDict


class SearchResult(TypedDict):
    title: str
    url: str
    content: str
    raw_content: str
    score: float


class ExtractedPage(TypedDict):
    url: str
    content: str


class Section(TypedDict):
    title: str
    content: str
    sources: list[str]   # evidence_ids for this section


class ResearchState(TypedDict):
    # --- Input ---
    query: str

    # --- Planner output ---
    plan: dict            # {topic, subtopics, outline: [{title, queries}], source_types}
    search_queries: list[str]
    plan_approved: bool
    plan_id: str
    clarifications: dict
    clarifying_questions: list[str]
    scout: dict  # pre-plan thinker web + Gemini scout

    # --- Researcher output ---
    search_results: list[SearchResult]
    extracted_pages: list[ExtractedPage]
    clean_content: list[str]
    claims: list[dict]    # [{text, evidence_ids: [url, ...], confidence}]

    # --- RAG ---
    run_id: str
    chunks_ingested: int
    retrieved_chunks: list[dict]

    # --- Factoid Pipeline ---
    factoids: list[dict]     # structured {type, value, confidence, source_quote, source_url, entities, topics}
    factoid_stats: dict      # {raw_tokens, factoid_tokens, num_factoids, reduction_pct, types}

    # --- Retriever Guard ---
    guard_stats: dict        # {total, passed, blocked, avg_score, domains}

    # --- Critic output ---
    findings: list[str]
    gaps: list[str]
    needs_more_research: bool
    replan: bool
    off_topic: bool
    abort_synthesis: bool

    # --- Adversary / CoVe / Research debt (Ultra steals) ---
    devil_advocate_done: bool
    socratic_hops: int
    socratic_reopen: bool
    socratic_done: bool
    adjudicated_claims: list
    contested_claims: list
    synthetic_claims: list
    research_debt: list
    confidence_note: str

    # --- Synthesizer output ---
    outline: list[dict]         # [{title, order}]
    sections: list[Section]     # progressively written sections
    evidence_map: dict[str, list[str]]  # evidence_id → [url, title]

    # --- Final output ---
    report: str
    markdown_path: str

    # --- Loop control ---
    iteration: int
    max_iterations: int
    mode: str
    status: str
    error: str
    job_id: str

    # --- Optional runtime controls (modes / autonomy / budgets) ---
    autonomy: str
    quality: dict
    budgets: dict
    mode_flags: dict


def initial_state(query: str, max_iterations: int = 6) -> ResearchState:
    import time
    import uuid
    import src.nodes as n
    n.MAX_ITERATIONS = max_iterations
    return {
        "query": query,
        "plan": {},
        "search_queries": [],
        "plan_approved": False,
        "plan_id": "",
        "clarifications": {},
        "clarifying_questions": [],
        "scout": {},
        "search_results": [],
        "extracted_pages": [],
        "clean_content": [],
        "claims": [],
        "run_id": uuid.uuid4().hex[:12],
        "chunks_ingested": 0,
        "retrieved_chunks": [],
        "factoids": [],
        "factoid_stats": {},
        "guard_stats": {},
        "findings": [],
        "gaps": [],
        "needs_more_research": False,
        "replan": False,
        "off_topic": False,
        "abort_synthesis": False,
        "devil_advocate_done": False,
        "socratic_hops": 0,
        "socratic_reopen": False,
        "socratic_done": False,
        "adjudicated_claims": [],
        "contested_claims": [],
        "synthetic_claims": [],
        "research_debt": [],
        "confidence_note": "",
        "outline": [],
        "sections": [],
        "evidence_map": {},
        "report": "",
        "markdown_path": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "mode": "standard",
        "status": "Starting research...",
        "error": "",
        "job_id": "",
        "autonomy": "L1",
        "quality": {
            "max_tokens_per_call": 8000,
            "max_search_results": 10,
            "max_extract_pages": 5,
            "thinker_enabled": False,
            "triangulation_enabled": False,
            "factoid_enabled": False,
        },
        "budgets": {
            "max_tokens": 100000,
            "max_cost_usd": 0.50,
            "max_time_s": 600,
            "max_tool_calls": 20,
            "max_iterations": max_iterations,
            "started_at": time.time(),
            "tool_calls": 0,
            "spent_usd": 0.0,
        },
        "mode_flags": {
            "recency_bias": False,
            "academic_bias": False,
            "structured_output": False,
            "vault_rag": True,
            "requires_temporal": False,
        },
    }
