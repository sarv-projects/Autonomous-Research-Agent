"""
Researcher agent — executes the research loop: search, extract, ingest, retrieve, analyze.

Uses the modular tool bus for search and extraction. Tools are auto-discovered
from the registry: Firecrawl (primary), Wikipedia (free), Built-in Scraper, Exa.
"""

import json

from src.llm import call_llm
from src.tools import execute_searches, extract_pages as tool_extract
from src.tools.registry import get_registry
from src.urlutil import canonical_url
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


def _llm_filter_chunks(chunks: list[dict], query: str) -> list[dict]:
    """LLM relevance pass: discard chunks that are topically irrelevant to the query.

    Mirrors Onyx's Stage-3 selection step — the primary hallucination entry point
    is chunks that score high on keyword/vector overlap but are semantically off-topic
    being passed straight into the analysis prompt.

    Uses the fast model with a tight token budget (max_tokens=200) so it doesn't
    add meaningful wall-time on free providers. Full fallback: if the call fails
    or returns nothing to keep, the original chunk list is returned unchanged.
    """
    if not chunks or not query:
        return chunks
    # Build compact chunk index (id, first 200 chars of text)
    index = [
        {"id": i, "text": (c.get("text") or "")[:200]}
        for i, c in enumerate(chunks)
    ]
    prompt = (
        f'Research query: "{query[:200]}"\n\n'
        "For each chunk, decide: KEEP (directly relevant to the query) or "
        "DISCARD (off-topic, generic, or only tangentially related).\n"
        'Return JSON: {"keep": [0, 2, 5, ...], "discard": [1, 3, 4, ...]}\n\n'
        + "\n".join(f'[{c["id"]}] {c["text"]}' for c in index)
    )
    try:
        raw = call_llm(
            "You are a strict relevance filter. Return only valid JSON with 'keep' and 'discard' integer lists.",
            prompt,
            model="fast",
            max_tokens=200,
        )
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        if "{" in cleaned:
            cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
        data = json.loads(cleaned)
        keep_ids = set(
            int(x) for x in (data.get("keep") or [])
            if isinstance(x, (int, str)) and str(x).isdigit()
        )
        if not keep_ids:
            return chunks  # model returned nothing to keep — safe fallback
        filtered = [chunks[i] for i in sorted(keep_ids) if i < len(chunks)]
        discarded = len(chunks) - len(filtered)
        if discarded > 0:
            print(f"  [relevance filter] {len(filtered)}/{len(chunks)} chunks kept ({discarded} discarded as off-topic)")
        return filtered
    except Exception as e:
        print(f"  [relevance filter] skipped ({e}) — using all {len(chunks)} chunks")
        return chunks


def _progress(stage: str, status: str = "", **kwargs) -> None:
    try:
        from src.engine.progress import get_progress
        get_progress().update(stage=stage, status=status or stage, **kwargs)
    except Exception:
        pass


@register("researcher_gather")
def researcher_gather(state: ResearchState) -> ResearchState:
    """Search the web and extract page content."""
    from src.engine.budget import (
        check_budgets,
        force_complete,
        record_tool_calls,
        sync_cost_from_metrics,
    )

    state["iteration"] = int(state.get("iteration") or 0) + 1
    sync_cost_from_metrics(state)
    ok, reason = check_budgets(state)
    if not ok:
        print(f"\n🔍 [Researcher] Budget stop: {reason}")
        return force_complete(state, reason)

    quality = state.get("quality") or {}
    flags = state.get("mode_flags") or {}
    max_results = int(quality.get("max_search_results") or 10)
    max_extract = int(quality.get("max_extract_pages") or 5)
    factoid_on = bool(quality.get("factoid_enabled", False))
    import os

    # Exa: modest boost, not 200-page firehoses (that was killing wall time)
    # Quality = top-N Exa with full text, not volume for volume's sake
    if os.getenv("EXA_API_KEY"):
        if state.get("mode") == "quick":
            max_results = min(max(max_results, 8), 10)
            max_extract = min(max(max_extract, 6), 8)
        elif state.get("mode") in ("deep", "academic", "ultra-long"):
            max_results = min(max(max_results, 10), 12)
            max_extract = min(max(max_extract, 10), 12)
        else:
            max_results = min(max(max_results, 8), 12)
            max_extract = min(max(max_extract, 8), 10)

    state["status"] = "Searching and extracting content..."
    _progress("researching", state["status"], iteration=state["iteration"])
    print(f"\n🔍 [Researcher] Iteration {state['iteration']} — gathering "
          f"(max_results={max_results}, extract={max_extract})")

    queries = list(state.get("search_queries") or [state["query"]])
    if not queries:
        queries = [state["query"]]

    # Cap query fan-out: each query = 1 Exa call; 8 queries × 22 = disaster
    queries = queries[:4]

    # Mode bias: rewrite queries for recency / academic focus (don't explode count)
    if flags.get("recency_bias"):
        queries = [f"{q} 2024 OR 2025 OR 2026 latest" for q in queries]
    if flags.get("academic_bias") or flags.get("force_arxiv"):
        # One arXiv-biased query only (not one per query)
        base = state.get("query") or queries[0]
        arxiv_q = f"{base[:100]} site:arxiv.org survey"
        if arxiv_q not in queries:
            queries = queries[:3] + [arxiv_q]

    # ── Vault reuse: seed results from past high-quality sources ──
    # Only keep vault hits that share topic keywords with the query (anti-contamination)
    vault_hits: list[dict] = []
    if flags.get("vault_rag", True):
        try:
            import re as _re
            q_words = {
                w for w in _re.findall(r"[a-zA-Z]{4,}", (state.get("query") or "").lower())
                if w not in {
                    "does", "what", "with", "from", "that", "this", "into", "about",
                    "cover", "methods", "best", "practices", "large", "language",
                }
            }
            vault = Vault()
            for q in queries[:3]:
                for hit in vault.search(q, k=min(5, max_results)):
                    blob = f"{hit.get('title','')} {hit.get('snippet','')} {hit.get('url','')}".lower()
                    if q_words and sum(1 for w in q_words if w in blob) < min(2, len(q_words)):
                        continue  # off-topic vault residue
                    vault_hits.append({
                        "title": hit.get("title", ""),
                        "url": hit.get("url", ""),
                        "content": hit.get("snippet", ""),
                        "raw_content": hit.get("snippet", ""),
                        "score": float(hit.get("quality_score", 5)) / 10.0,
                        "source": "vault",
                        "guard_score": float(hit.get("quality_score", 5)),
                    })
            if vault_hits:
                print(f"  Vault reuse: {len(vault_hits)} on-topic cached sources")
        except Exception:
            vault_hits = []

    registry = get_registry()
    available = [t.name for t in registry.list_all()]
    print(f"  Tools available: {available}")

    # Live web search (tool bus)
    results = execute_searches(queries, max_results=max_results)
    record_tool_calls(state, n=len(queries))

    # Deep/academic: one Exa arXiv pass only (skip slow/flaky mineru when Exa works)
    if flags.get("academic_bias") or flags.get("force_arxiv"):
        if os.getenv("EXA_API_KEY"):
            try:
                from src.tools.adapters.exa import exa_search
                aq = f"{state['query'][:120]} site:arxiv.org"
                extra = exa_search(aq, max_results=min(6, max_results))
                if extra:
                    print(f"  Exa arXiv: +{len(extra)} hits")
                    results = list(results) + extra
                    record_tool_calls(state, n=1)
            except Exception as e:
                print(f"  Exa arXiv skipped: {e}")
        else:
            try:
                from src.tools.adapters.mineru import mineru_search
                arxiv = mineru_search(state["query"], max_results=min(5, max_results))
                if arxiv:
                    print(f"  Academic: +{len(arxiv)} arXiv hits")
                    results = list(results) + arxiv
                    record_tool_calls(state, n=1)
            except Exception as e:
                print(f"  Academic arXiv search skipped: {e}")

    # Hard cap total search hits kept (Exa can dump 100+ across queries)
    hard_cap = max(max_results * 2, 20)
    if len(results) > hard_cap:
        results = sorted(results, key=lambda r: float(r.get("score") or 0), reverse=True)[:hard_cap]
        print(f"  Capped search pool to top {hard_cap} by score")

    # Merge vault + live (URL dedup, live wins on conflict for freshness)
    seen_urls: set[str] = set()
    merged: list[dict] = []
    for r in results + vault_hits:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append(r)
    results = merged

    # ── Retriever Guard ──
    if results:
        print(f"  Found {len(results)} raw results via {results[0].get('source', 'unknown')}")
        before_count = len(results)
        # P0.4: pass the query so the guard can block real-but-irrelevant hits
        results, guard_stats = filter_results(results, min_score=3.0, topic=state.get("query", ""))
        state["guard_stats"] = guard_stats
        print(f"  Guard: {before_count} → {len(results)} passed"
              f" ({guard_stats['blocked']} blocked, avg score {guard_stats['avg_score']})")
        if guard_stats.get("off_topic_blocked"):
            print(f"    Off-topic blocked: {guard_stats['off_topic_blocked']}")
        if guard_stats.get("domains", {}).get("blocked"):
            print(f"    Blocked: {', '.join(guard_stats['domains']['blocked'])}")
    else:
        print("  ⚠️  No search results from any tool")
        state["guard_stats"] = {"total": 0, "passed": 0, "blocked": 0, "avg_score": 0}

    # Store live results in vault for future reuse
    if results:
        try:
            Vault().store_results(
                [r for r in results if r.get("source") != "vault"],
                queries=queries,
            )
        except Exception:
            pass

    state["search_results"] = results
    for r in results[:3]:
        print(f"    • [{r.get('guard_score', '?')}] {r.get('title', '')[:60]}")

    pages_scanned = len(results)
    _progress(
        "researching",
        f"Found {len(results)} sources",
        iteration=state["iteration"],
        pages_scanned=pages_scanned,
        sources_count=len(results),
    )
    try:
        from src.engine.progress import get_progress
        get_progress().think("next", f"Extracting up to {max_extract} pages")
    except Exception:
        pass

    # Prefer Exa full text already in results — no re-extract round-trip
    top = results[:max_extract]
    already_full = {
        r["url"] for r in top
        if r.get("url") and len(r.get("raw_content") or "") > 800
    }
    need_extract = [r["url"] for r in top if r.get("url") and r["url"] not in already_full]
    extracted = tool_extract(need_extract) if need_extract else []
    for r in top:
        if r.get("url") in already_full:
            extracted.append({
                "url": r["url"],
                "content": r.get("raw_content") or r.get("content", ""),
                "title": r.get("title", ""),
                "source": r.get("source", "exa"),
            })
    record_tool_calls(state, n=1 if need_extract else 0)
    state["extracted_pages"] = extracted
    print(f"  Content pages: {len(extracted)} ({len(already_full)} from Exa text, "
          f"{len(need_extract)} extracted)")
    _progress("researching", f"Pages ready: {len(extracted)}",
              pages_scanned=max(pages_scanned, len(extracted)),
              iteration=state["iteration"])

    # Ingest only top pages (not entire 100+ result dump)
    pages = []
    seen_page_urls: set[str] = set()
    for r in top:
        raw = r.get("raw_content", "") or r.get("content", "")
        url = r.get("url", "")
        if raw and url not in seen_page_urls:
            seen_page_urls.add(url)
            pages.append({
                "url": url, "title": r.get("title", ""),
                "content": raw[:12000], "source_type": "web",
            })
    for p in extracted:
        content = p.get("content", "")
        url = p.get("url", "")
        if content and url not in seen_page_urls:
            seen_page_urls.add(url)
            pages.append({
                "url": url, "title": p.get("title", ""),
                "content": content[:12000], "source_type": "web_extracted",
            })

    if pages:
        # Factoids: skip after iter 1 and keep tiny (each call is a free-model stall)
        if not factoid_on or int(state.get("iteration") or 1) > 1:
            if not factoid_on:
                print("  Skipping factoid extraction (disabled by quality dial)")
            else:
                print("  Skipping factoids after iter 1 (speed)")
            all_factoids = []
        else:
            sample = pages[:3]
            print(f"  Extracting factoids from {len(sample)} pages (speed-capped)...")
            all_factoids = extract_from_pages(sample, max_pages=3, max_llm_calls=1)

        from src.rag.factoid import deduplicate_factoids
        existing_factoids = state.get("factoids") or []
        combined = deduplicate_factoids(list(existing_factoids) + all_factoids)
        state["factoids"] = combined
        state["factoid_stats"] = token_reduction_stats(pages, all_factoids)
        stats = state["factoid_stats"]
        print(f"  Factoids: {len(all_factoids)} new → {len(combined)} total, "
              f"{stats['factoid_tokens']} tokens ({stats['reduction_pct']:.0f}% reduction"
              f" vs {stats['raw_tokens']} raw)")
        _progress("researching", f"Factoids={len(combined)}",
                  factoids_count=len(combined), iteration=state["iteration"])

        ingested = ingest_documents(pages, run_id=state.get("run_id", "default"))
        if all_factoids:
            factoid_pages = [
                {
                    "url": (f.get("source_urls") or [f.get("source_url", "factoid://")])[0]
                           or f"factoid://{f.get('id', '')}",
                    "title": f"[Factoid: {f.get('type', '')}] {f.get('value', '')[:80]}",
                    "content": f.get("value", ""),
                    "source_type": "factoid",
                }
                for f in all_factoids
            ]
            # Same run_id so hybrid retrieve isolation still sees factoids
            ingested += ingest_documents(
                factoid_pages, run_id=state.get("run_id", "default")
            )
        state["chunks_ingested"] = int(state.get("chunks_ingested") or 0) + ingested
        print(f"  Ingested {ingested} chunks (total: {state['chunks_ingested']})")
        state["clean_content"] = [p["content"][:500] for p in pages[:5] if p.get("content")]
    else:
        state["status"] = "No content found"
        print("  ⚠️  No content to ingest")

    sync_cost_from_metrics(state)
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
    # P0.1: always filter by run_id to prevent cross-run contamination
    factoids = state.get("factoids", [])
    run_id = state.get("run_id", "")
    results = hybrid_retrieve(query, k=12, factoids=factoids, run_id=run_id)

    # ── LLM Relevance Filter (Onyx Stage-3) ──────────────────────────────────
    # Discard chunks that scored high on keyword/vector overlap but are
    # semantically off-topic. This is the #1 hallucination entry point in
    # comparable systems (Onyx paper, Gap 1 in eval). Only applied when we
    # have enough chunks that filtering is worthwhile (>4).
    base_query = state.get("query", "")
    if len(results) > 4:
        results = _llm_filter_chunks(results, base_query)
    state["retrieved_chunks"] = results

    # Accumulate run-wide corpus so later adjudication can verify claims
    # extracted in EARLIER iterations too (chunks are overwritten each loop).
    # Dedup by canonical URL so html/pdf/abs variants of one paper count once.
    run_corpus = list(state.get("run_corpus") or [])
    seen_chunk = {canonical_url(c.get("url") or "") for c in run_corpus}
    for r in results:
        u = canonical_url(r.get("url") or "")
        if u and u not in seen_chunk:
            seen_chunk.add(u)
            run_corpus.append(r)
    state["run_corpus"] = run_corpus

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


    # Keep analyze prompt small — free models stall on 30k+ contexts
    if len(content_text) > 12000:
        content_text = content_text[:12000]

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

    # Store claims with evidence mapping — only URLs actually retrieved this run.
    # LLM-invented evidence IDs (real-looking but never fetched) are dropped here
    # so they cannot reach evidence_map, Bedrock, or Sources (P0.4 fix).
    known_urls: set[str] = set()
    for c in state.get("retrieved_chunks") or []:
        u = canonical_url(c.get("url") or "")
        if u:
            known_urls.add(u)
    for r in state.get("search_results") or []:
        u = canonical_url(r.get("url") or "")
        if u:
            known_urls.add(u)
    for p in state.get("extracted_pages") or []:
        u = canonical_url(p.get("url") or "")
        if u:
            known_urls.add(u)
    for c in claims:
        for url in c.get("evidence_ids", []):
            cu = canonical_url(url)
            if cu and cu in known_urls:
                state["evidence_map"].setdefault(cu, []).append(c.get("text", "")[:100])

    state["claims"] = state.get("claims", []) + claims
    state["gaps"] = gaps
    state["status"] = f"Extracted {len(findings)} findings, {len(claims)} claims, {len(gaps)} gaps"
    print(f"  Findings: {len(findings)}, Claims: {len(claims)}, Gaps: {len(gaps)}")
    try:
        from src.engine.progress import get_progress
        p = get_progress()
        for f in findings[:3]:
            p.think("learned", str(f)[:200])
        for g in gaps[:3]:
            p.think("gap", str(g)[:200])
        p.update(
            findings_count=len(state.get("findings") or []),
            sources_count=len(state.get("evidence_map") or {}),
            status=state["status"],
        )
    except Exception:
        pass
    return state
