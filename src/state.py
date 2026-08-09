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


def initial_state(query: str, max_iterations: int = 6) -> ResearchState:
    import uuid
    import src.nodes as n
    n.MAX_ITERATIONS = max_iterations
    return {
        "query": query,
        "plan": {},
        "search_queries": [],
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
    }
