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


class ResearchState(TypedDict):
    # --- Input ---
    query: str

    # --- Research plan ---
    search_queries: list[str]

    # --- Results ---
    search_results: list[SearchResult]
    extracted_pages: list[ExtractedPage]
    clean_content: list[str]

    # --- Analysis ---
    findings: list[str]
    needs_more_research: bool

    # --- Output ---
    report: str
    markdown_path: str

    # --- Loop control ---
    iteration: int
    status: str
    error: str


def initial_state(query: str) -> ResearchState:
    return {
        "query": query,
        "search_queries": [],
        "search_results": [],
        "extracted_pages": [],
        "clean_content": [],
        "findings": [],
        "needs_more_research": False,
        "report": "",
        "markdown_path": "",
        "iteration": 0,
        "status": "Starting research...",
        "error": "",
    }
