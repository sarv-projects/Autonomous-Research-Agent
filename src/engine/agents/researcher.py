"""
Researcher agent — executes the research loop: search, extract, ingest, retrieve, analyze.

Uses the modular tool bus for search and extraction. Tools are auto-discovered
from the registry: Firecrawl (primary), Wikipedia (free), Built-in Scraper, Exa.
"""

import json

from src.llm import call_llm
from src.tools import execute_searches, extract_pages as tool_extract
from src.tools.registry import get_registry
from src.rag.pipeline import ingest_documents, retrieve_chunks
from src.rag.factoid import extract_from_pages, token_reduction_stats
from src.rag.guard import filter_results, retry_pyramid_filter
from src.rag.hybrid import hybrid_retrieve
from src.rag.vault import Vault
from src.state import ResearchState
from .registry import register

RESEARCHER_SYSTEM = (
    "You are a thorough research analyst. Extract factual claims from sources, "
    "identify supporting evidence, and flag contradictions. Return valid JSON."
)


@register("researcher_gather")
def researcher_gather(state: ResearchState) -> ResearchState:
    """Search the web and extract page content."""
    state["iteration"] += 1
    state["status"] = "Searching and extracting content..."
    print(f"\n🔍 [Researcher] Iteration {state['iteration']} — gathering")

    queries = state.get("search_queries", [state["query"]])
    if not queries:
        queries = [state["query"]]

    # Search using tool bus (Firecrawl > Wikipedia > Built-in fallback)
    registry = get_registry()
    available = [t.name for t in registry.list_all()]
    print(f"  Tools available: {available}")

    results = execute_searches(queries, max_results=5)

    # ── Retriever Guard (Phase G): filter low-quality sources ──
    if results:
        print(f"  Found {len(results)} raw results via {results[0].get('source', 'unknown')}")
        before_count = len(results)
        results, guard_stats = filter_results(results, min_score=3.0)
        state["guard_stats"] = guard_stats
        print(f"  Guard: {before_count} → {len(results)} passed"
              f" ({guard_stats['blocked']} blocked, avg score {guard_stats['avg_score']})")
        if guard_stats["domains"]["blocked"]:
            print(f"    Blocked: {', '.join(guard_stats['domains']['blocked'])}")
    else:
        print("  ⚠️  No search results from any tool")
        state["guard_stats"] = {"total": 0, "passed": 0, "blocked": 0, "avg_score": 0}

    # ── Vault (Phase H): store results for cross-run reuse ──
    if results:
        try:
            vault = Vault()
            vault.store_results(results, queries=queries)
        except Exception:
            pass  # Vault is best-effort

    state["search_results"] = results

    if results:
        for r in results[:3]:
            score = r.get("guard_score", "?")
            print(f"    • [{score}] {r.get('title', '')[:60]}")

    # Extract pages using tool bus
    urls = [r["url"] for r in results[:8]]
    extracted = tool_extract(urls)
    state["extracted_pages"] = extracted
    print(f"  Extracted {len(extracted)} pages")

    # Ingest into RAG
    pages = []
    for r in results[:12]:
        raw = r.get("raw_content", "") or r.get("content", "")
        if raw:
            pages.append({
                "url": r.get("url", ""), "title": r.get("title", ""),
                "content": raw, "source_type": "web",
            })
    for p in extracted:
        content = p.get("content", "")
        if content:
            pages.append({
                "url": p.get("url", ""), "title": p.get("title", ""),
                "content": content, "source_type": "web_extracted",
            })

    if pages:
        # ── Factoid Extraction (Phase F) — skip if too many pages or quick mode ──
        mode_config = state.get("mode", "standard")
        if mode_config == "quick" or len(pages) > 12:
            print(f"  Skipping factoid extraction ({len(pages)} pages, mode={mode_config})")
            all_factoids = []
        else:
            print(f"  Extracting factoids from {len(pages)} pages (batched)...")
            all_factoids = extract_from_pages(pages, max_pages=5, max_llm_calls=2)
        # Cross-iteration dedup: merge with existing and re-deduplicate
        from src.rag.factoid import deduplicate_factoids
        existing_factoids = state.get("factoids", [])
        combined = deduplicate_factoids(existing_factoids + all_factoids)
        state["factoids"] = combined
        state["factoid_stats"] = token_reduction_stats(pages, all_factoids)
        stats = state["factoid_stats"]
        print(f"  Factoids: {len(all_factoids)} new → {len(combined)} total, "
              f"{stats['factoid_tokens']} tokens ({stats['reduction_pct']:.0f}% reduction"
              f" vs {stats['raw_tokens']} raw)")

        # Ingest chunks into RAG
        ingested = ingest_documents(pages, run_id=state.get("run_id", "default"))

        # Also ingest factoids as synthetic pages for retrieval
        # Use just the value as content (not JSON wrapper) for clean embeddings
        if all_factoids:
            factoid_pages = [
                {
                    "url": f.get("source_urls", [f.get("source_url", "factoid://")])[0]
                           or f"factoid://{f.get('id', '')}",
                    "title": f"[Factoid: {f.get('type', '')}] {f.get('value', '')[:80]}",
                    "content": f.get("value", ""),
                    "source_type": "factoid",
                }
                for f in all_factoids
            ]
            factoid_ingested = ingest_documents(factoid_pages, run_id=f"{state.get('run_id', 'default')}_factoids")
            ingested += factoid_ingested
        state["chunks_ingested"] = state.get("chunks_ingested", 0) + ingested
        print(f"  Ingested {ingested} chunks (total: {state['chunks_ingested']})")
        state["clean_content"] = [p["content"][:500] for p in pages[:5] if p.get("content")]
    else:
        state["status"] = "No content found"
        print("  ⚠️  No content to ingest")

    return state


@register("researcher_analyze")
def researcher_analyze(state: ResearchState) -> ResearchState:
    """Retrieve from RAG and extract claims from the retrieved chunks."""
    state["status"] = "Retrieving and analyzing..."
    print(f"\n🔍 [Researcher] Analyzing")

    # Retrieve from RAG
    query = state["query"]
    if state.get("findings"):
        query = query + " " + " ".join(state["findings"][-3:])
    if state.get("gaps"):
        query = query + " " + " ".join(state["gaps"][-3:])

    # ── Hybrid Retrieval (Phase H): dense + sparse + factoid fusion ──
    factoids = state.get("factoids", [])
    results = hybrid_retrieve(query, k=12, factoids=factoids)
    state["retrieved_chunks"] = results

    if results:
        retrieved_tokens = sum(len(r.get("text", "").split()) * 1.3 for r in results)
        raw_est = sum(len(p.get("content", "").split()) * 1.3 for p in state.get("extracted_pages", []))
        raw_est += sum(len((r2.get("raw_content") or r2.get("content", "")).split()) * 1.3
                       for r2 in state.get("search_results", []))
        reduction = (1 - retrieved_tokens / max(raw_est, 1)) * 100
        print(f"  Retrieved {len(results)} chunks ({retrieved_tokens:.0f} tokens, {reduction:.0f}% vs raw)")

        # Extract claims
        content_text = "\n\n".join(
            f"[{r.get('title','') or r.get('url','')}]\n{r.get('text','')[:600]}"
            for r in results[:10]
        )
    else:
        content_text = "\n".join(state.get("clean_content", ["No content."]))
        print("  ⚠️  No RAG chunks — using raw fallback")

    if len(content_text) > 30000:
        content_text = content_text[:30000]

    prompt = f"""Extract key findings and claims from this research content.

Query: "{state['query']}"

Content:
{content_text}

Return a JSON object with:
  - "findings": list of 5-10 key findings (each a string)
  - "claims": list of claim objects: {{"text": "...", "evidence_ids": ["url1", "url2"], "confidence": "high"|"medium"|"low"}}
  - "gaps": list of unanswered questions or missing information
  - "confidence": overall confidence: "high", "medium", or "low\""""

    result = call_llm(RESEARCHER_SYSTEM, prompt)
    try:
        analysis = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        analysis = {"findings": [content_text[:500]], "claims": [], "gaps": [], "confidence": "low"}

    findings = analysis.get("findings", [])
    gaps = analysis.get("gaps", [])
    claims = analysis.get("claims", [])

    # Merge findings
    existing = set(state.get("findings", []))
    for f in findings:
        if f not in existing:
            state["findings"].append(f)
            existing.add(f)

    # Store claims with evidence mapping
    for c in claims:
        for url in c.get("evidence_ids", []):
            state["evidence_map"].setdefault(url, []).append(c.get("text", "")[:100])

    state["claims"] = state.get("claims", []) + claims
    state["gaps"] = gaps
    state["status"] = f"Extracted {len(findings)} findings, {len(claims)} claims, {len(gaps)} gaps"
    print(f"  Findings: {len(findings)}, Claims: {len(claims)}, Gaps: {len(gaps)}")
    return state
