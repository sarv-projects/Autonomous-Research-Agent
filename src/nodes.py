"""LangGraph node functions for the research agent."""


import json
import time

from src.llm import call_llm
from src.search import parallel_search, extract_content
from src.state import ResearchState
from src.rag.pipeline import ingest_documents, retrieve_chunks

MAX_ITERATIONS = 3


def parse_query(state: ResearchState) -> ResearchState:
    """Analyze the user's query to understand what to research."""
    state["status"] = "Analyzing your query..."
    print(f"\n🔍 [{state['iteration']}] {state['status']}")

    prompt = f"""Analyze this research query and identify:
1. The main topic
2. 3-5 key subtopics or angles to investigate
3. What types of sources would be most valuable

Query: "{state['query']}"

Return your analysis as a JSON object with keys: "topic", "subtopics" (list), "source_types" (list)"""

    result = call_llm(
        "You are an expert research analyst. Always return valid JSON.",
        prompt,
    )

    try:
        analysis = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        analysis = {"topic": state["query"], "subtopics": [], "source_types": []}

    state["findings"] = [f"Research topic: {analysis.get('topic', state['query'])}"]
    state["status"] = f"Parsed query: {analysis.get('topic', state['query'])}"
    print(f"  Topic: {analysis.get('topic', state['query'])}")
    return state


def plan_searches(state: ResearchState) -> ResearchState:
    """Generate search queries based on current state."""
    state["iteration"] += 1
    state["status"] = f"Planning search queries (iteration {state['iteration']})..."
    print(f"\n🔍 [{state['iteration']}] {state['status']}")

    findings_so_far = "\n".join(state["findings"]) if state["findings"] else "No findings yet."

    prompt = f"""Based on the research so far, generate 3-5 specific search queries to find the most relevant information.

Original query: "{state['query']}"
Findings so far: {findings_so_far}
Iteration: {state['iteration']}

Return a JSON list of search query strings only. Example: ["query1", "query2", "query3"]
Make each query specific and targeted. Vary the angle of each query."""

    result = call_llm(
        "You are a research strategist. Return only valid JSON.",
        prompt,
    )

    try:
        queries = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        if not isinstance(queries, list):
            queries = [state["query"]]
    except (json.JSONDecodeError, TypeError):
        queries = [state["query"]]

    state["search_queries"] = queries[:5]
    print(f"  Queries: {state['search_queries']}")
    return state


def execute_searches(state: ResearchState) -> ResearchState:
    """Run all planned searches in parallel."""
    state["status"] = "Searching the web..."
    print(f"\n🔍 {state['status']}")

    if not state["search_queries"]:
        state["search_queries"] = [state["query"]]

    results = parallel_search(state["search_queries"], max_results=5)
    state["search_results"] = results
    state["status"] = f"Found {len(results)} results"
    print(f"  Found {len(results)} unique results")

    for r in results[:3]:
        print(f"    • {r['title']}")
    return state


def extract_pages(state: ResearchState) -> ResearchState:
    """Extract full content from top search results."""
    state["status"] = "Extracting content from top pages..."
    print(f"\n🔍 {state['status']}")

    urls = [r["url"] for r in state["search_results"][:8]]
    extracted = extract_content(urls)

    state["extracted_pages"] = extracted
    state["status"] = f"Extracted {len(extracted)} pages"
    print(f"  Extracted {len(extracted)} pages")
    return state


def ingest_chunks(state: ResearchState) -> ResearchState:
    """Chunk, embed, and store extracted pages in the vector database.

    Replaces the old deduplicate_content node with proper RAG ingestion.
    """
    state["status"] = "Ingesting content into vector store..."
    print(f"\n🔍 {state['status']}")

    # Build pages list from search results + extracted pages
    pages = []
    for r in state["search_results"][:12]:
        raw = r.get("raw_content", "") or r.get("content", "")
        if raw:
            pages.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "content": raw,
                "source_type": "web",
            })

    for p in state["extracted_pages"]:
        content = p.get("content", "")
        if content:
            pages.append({
                "url": p.get("url", ""),
                "title": p.get("title", "") if hasattr(p, "get") and "title" in p else "",
                "content": content,
                "source_type": "web_extracted",
            })

    if not pages:
        state["status"] = "No content to ingest"
        return state

    run_id = state.get("run_id", "default_run")
    ingested = ingest_documents(pages, run_id=run_id)
    state["chunks_ingested"] = ingested

    # Also keep a text summary for backward compat
    state["clean_content"] = [p["content"][:500] for p in pages[:5] if p.get("content")]

    state["status"] = f"Ingested {ingested} chunks into vector store"
    print(f"  Chunked & embedded {ingested} chunks from {len(pages)} pages")
    return state


def retrieve_for_analysis(state: ResearchState) -> ResearchState:
    """Retrieve relevant chunks from the vector store for analysis."""
    state["status"] = "Retrieving relevant chunks from vector store..."
    print(f"\n🔍 {state['status']}")

    # Use the current query + latest findings for retrieval
    query = state["query"]
    if state["findings"]:
        query = query + " " + " ".join(state["findings"][-3:])

    results = retrieve_chunks(query, k=10)
    state["retrieved_chunks"] = results

    if results:
        retrieved_tokens = sum(len(r.get("text", "").split()) * 1.3 for r in results)
        # Estimate raw page dump size for comparison
        raw_estimate = sum(
            len(p.get("content", "").split()) * 1.3
            for p in state.get("extracted_pages", [])
        )
        raw_estimate += sum(
            len(r.get("raw_content", "") or r.get("content", "")).split() * 1.3
            for r in state.get("search_results", [])
        )
        reduction = (1 - retrieved_tokens / max(raw_estimate, 1)) * 100
        print(f"  Retrieved {len(results)} chunks ({retrieved_tokens:.0f} est. tokens)")
        print(f"  Token reduction vs raw dump: {reduction:.0f}% (was {raw_estimate:.0f} → {retrieved_tokens:.0f})")
        for r in results[:3]:
            print(f"    • {r.get('title','')[:50] or r.get('url','')[:50]}")
    else:
        print("  ⚠️  No chunks retrieved — using raw content fallback")

    return state


def analyze_findings(state: ResearchState) -> ResearchState:
    """Extract key findings from retrieved RAG chunks (or fall back to raw content)."""
    state["status"] = "Analyzing findings..."
    print(f"\n🔍 {state['status']}")

    # Prefer RAG-retrieved chunks
    retrieved = state.get("retrieved_chunks", [])
    if retrieved:
        content_summary = "\n\n".join(
            f"[Source: {r.get('title','') or r.get('url','')}]\n{r.get('text','')[:600]}"
            for r in retrieved[:10]
        )
        print(f"  Using {len(retrieved)} RAG-retrieved chunks ({len(content_summary)} chars)")
    else:
        # Fallback: use raw content
        content_summary = "\n".join(state.get("clean_content", []))
        if not content_summary:
            content_summary = "No content available."

    if len(content_summary) > 40000:
        content_summary = content_summary[:40000]

    prompt = f"""Based on this research content, extract key findings.

Original query: "{state['query']}"

Content:
{content_summary}

Return a JSON object with:
- "findings": list of 5-10 key findings (each a string)
- "gaps": list of unanswered questions or gaps (each a string)
- "confidence": "high", "medium", or "low" based on source quality and consistency"""

    result = call_llm(
        "You are a research analyst extracting insights. Return valid JSON.",
        prompt,
    )

    try:
        analysis = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        analysis = {"findings": [content_summary[:500]], "gaps": [], "confidence": "low"}

    findings = analysis.get("findings", [])
    gaps = analysis.get("gaps", [])

    # Merge with existing findings
    existing = set(state["findings"])
    for f in findings:
        if f not in existing:
            state["findings"].append(f)
            existing.add(f)

    state["status"] = f"Extracted {len(findings)} findings, {len(gaps)} gaps"
    print(f"  Found {len(findings)} key findings, {len(gaps)} gaps")
    for f in findings[:3]:
        print(f"    • {f[:80]}...")
    return state


def evaluate_research(state: ResearchState) -> ResearchState:
    """Decide if more research is needed."""
    state["status"] = "Evaluating research completeness..."
    print(f"\n🔍 {state['status']}")

    findings_text = "\n".join(state["findings"])

    prompt = f"""Evaluate if the research is complete enough to generate a report.

Original query: "{state['query']}"
Iteration: {state['iteration']} (max {MAX_ITERATIONS})

Findings so far:
{findings_text}

Consider:
1. Are there major aspects of the query not addressed?
2. Is the information consistent?
3. Is there enough depth for a useful report?
4. Are sources credible?

Return a JSON object with:
- "complete": true or false
- "reason": brief explanation
- "confidence": "high", "medium", "low"
"""

    result = call_llm(
        "You are a research quality evaluator. Return valid JSON.",
        prompt,
    )

    try:
        evaluation = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        evaluation = {"complete": True, "reason": "Unable to evaluate", "confidence": "low"}

    is_complete = evaluation.get("complete", False)
    reason = evaluation.get("reason", "")

    # Force stop after max iterations
    if state["iteration"] >= MAX_ITERATIONS:
        is_complete = True
        reason = f"Reached maximum iterations ({MAX_ITERATIONS})"

    state["needs_more_research"] = not is_complete
    state["status"] = f"Research {'complete' if is_complete else 'needs more'}: {reason}"
    print(f"  Research {'✅ complete' if is_complete else '🔄 needs more'}")
    print(f"  Reason: {reason}")
    return state


def synthesize_report(state: ResearchState) -> ResearchState:
    """Generate the final structured report."""
    state["status"] = "Synthesizing research report..."
    print(f"\n🔍 {state['status']}")

    findings_text = "\n".join(f"- {f}" for f in state["findings"])
    sources_text = "\n".join(f"- [{r['title']}]({r['url']})" for r in state["search_results"][:10])

    prompt = f"""Generate a comprehensive, well-structured research report.

Original Query: "{state['query']}"

Findings:
{findings_text}

Sources:
{sources_text}

Format the report in Markdown with these sections:
# Research Report: [Title]
**Date**: {time.strftime("%Y-%m-%d %H:%M")}

## Overview
2-3 paragraph summary of the research.

## Key Points
5-10 bullet points with the most important findings.

## Detailed Findings
2-3 paragraphs diving deeper into the most significant findings.

## Sources/References
Numbered list of all sources with titles and URLs.

## Actionable Insights
3-5 specific, actionable takeaways based on the research.

## Methodology
Brief note on how the research was conducted (searches, sources used).

Make the report thorough, well-organized, and useful. Write in a professional tone."""

    report = call_llm(
        "You are a professional research report writer. Produce thorough, well-structured Markdown.",
        prompt,
    )

    state["report"] = report
    state["status"] = "Report generated"
    print(f"  Report generated ({len(report)} chars)")
    return state


def export_report(state: ResearchState) -> ResearchState:
    from src.export import save_markdown

    state["status"] = "Exporting report..."
    print(f"\n🔍 {state['status']}")

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in state["query"])[:50]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_filename = f"research_{safe_name}_{timestamp}"

    md_path = save_markdown(state["report"], base_filename)
    state["markdown_path"] = md_path
    print(f"  ✓ Report saved: {md_path}")

    state["status"] = "Report exported"
    return state
