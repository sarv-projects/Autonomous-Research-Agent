"""LangGraph node functions for the research agent."""

import json
import time

from src.llm import call_llm
from src.search import parallel_search, extract_content
from src.state import ResearchState

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


def deduplicate_content(state: ResearchState) -> ResearchState:
    """Remove duplicate or irrelevant content using the LLM."""
    state["status"] = "Deduplicating and filtering content..."
    print(f"\n🔍 {state['status']}")

    all_texts = []
    for r in state["search_results"][:8]:
        raw = r.get("raw_content", "") or r.get("content", "")
        title = r.get("title", "")
        if raw:
            all_texts.append(f"--- {title} ---\n{raw[:800]}")

    for p in state["extracted_pages"][:3]:
        content = p.get("content", "")[:1000]
        if content:
            all_texts.append(content)

    if not all_texts:
        state["status"] = "No content to deduplicate"
        return state

    combined = "\n\n".join(all_texts)
    if len(combined) > 25000:
        combined = combined[:25000]

    prompt = f"""Review the following research content and:
1. Remove duplicate information
2. Remove irrelevant content
3. Keep only valuable, unique information
4. Preserve source titles and URLs where available

Content to filter:
{combined}

Return a JSON list of strings, each being a unique, relevant piece of information.
Example: ["fact 1", "fact 2", "fact 3"]"""

    result = call_llm(
        "You are a research assistant that removes noise and keeps signal. Return valid JSON.",
        prompt,
    )

    try:
        cleaned = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        if not isinstance(cleaned, list):
            cleaned = [combined[:1000]]
    except (json.JSONDecodeError, TypeError):
        cleaned = [combined[:1000]]

    state["clean_content"] = cleaned
    state["status"] = f"Cleaned to {len(cleaned)} unique pieces"
    print(f"  Reduced to {len(cleaned)} unique pieces of information")
    return state


def analyze_findings(state: ResearchState) -> ResearchState:
    """Extract key findings from the cleaned content."""
    state["status"] = "Analyzing findings..."
    print(f"\n🔍 {state['status']}")

    content_summary = "\n".join(state["clean_content"])
    if not content_summary:
        content_summary = "No content available."

    # Truncate
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
