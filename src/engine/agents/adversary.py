"""
Adversarial / Socratic steal from Ultra blueprint:

  devil_advocate_gather  — search for counter-evidence, limits, retractions
  claim_adjudicator      — CoVe-lite + optional one Socratic re-gather hop
"""

from __future__ import annotations

import json
import re

from src.llm import call_llm
from src.rag.guard import STOP_WORDS
from src.state import ResearchState
from src.urlutil import canonical_url
from .registry import register


def _progress(stage: str, status: str = "", **kwargs) -> None:
    try:
        from src.engine.progress import get_progress
        get_progress().update(stage=stage, status=status or stage, **kwargs)
    except Exception:
        pass


def _corpus(state: ResearchState) -> str:
    parts: list[str] = []
    # Run-wide accumulated chunks (all iterations) — primary source
    for c in state.get("run_corpus") or []:
        parts.append(c.get("text") or "")
    for c in state.get("retrieved_chunks") or []:
        parts.append(c.get("text") or "")
    for p in (state.get("extracted_pages") or [])[:25]:
        parts.append((p.get("content") or "")[:3000])
    for r in (state.get("search_results") or [])[:30]:
        parts.append((r.get("raw_content") or r.get("content") or "")[:1500])
    parts.extend(state.get("findings") or [])
    return " ".join(parts).lower()


def _claim_support(
    claim_text: str,
    corpus: str,
    evidence_ids: list,
    known_urls: set[str] | None = None,
    url_text: dict[str, str] | None = None,
) -> tuple[str, float, list[str]]:
    """Return (status, score, verified_eids). status: supported | contested | synthetic.

    Evidence verification (P0.4 fix):
      - Status is decided by corpus match (the claim's words appearing in what
        this run actually read) — as before.
      - The claim's verifiable evidence URLs are FILTERED to URLs actually
        retrieved this run; LLM-fabricated IDs never make it into the returned
        evidence list (so they can't reach Bedrock/Sources).
      - If a claim cites a real retrieved URL whose own text does NOT support
        the claim (real-but-irrelevant), it is demoted to contested.
    """
    text = (claim_text or "").strip()
    if not text:
        return "synthetic", 0.0, []

    # factoid:// and empty IDs are not verifiable URLs — treated as "no evidence"
    real_eids = [canonical_url(e) for e in (evidence_ids or [])[:5] if e and not e.startswith("factoid:")]
    # Keep only URLs actually retrieved this run
    verified_eids: list[str] = []
    for eid in real_eids:
        if known_urls is not None and eid in known_urls:
            verified_eids.append(eid)

    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    if len(words) < 4:
        # Short claims keep their verified evidence (just weak status)
        return "synthetic", 0.2, verified_eids

    # ── Corpus-wide lexical match (claim appears in what we read) ──
    # Skip stopword-heavy trigrams ("as well as") so generic phrasing alone
    # cannot mark a claim supported.
    phrases = []
    for i in range(len(words) - 2):
        ph = words[i : i + 3]
        if sum(1 for w in ph if w in STOP_WORDS) >= 2:
            continue
        phrases.append(" ".join(ph))
    phrase_hits = sum(1 for ph in phrases[:8] if ph in corpus)
    word_hits = sum(1 for w in words[:14] if w in corpus)
    # Normalize by the claim's own length so short claims with near-total word
    # overlap (e.g. the core topic sentence) aren't unfairly penalized by a
    # fixed 14-word denominator.
    score = min(1.0, phrase_hits * 0.35 + (word_hits / max(4, len(words[:14]))) * 0.65)

    # ── Per-URL topicality: does the cited page's own text support the claim? ──
    url_supports = False
    src_seen = False
    for eid in verified_eids:
        src = ((url_text or {}).get(eid, "") or "")[:4000].lower()
        if src:
            src_seen = True
            src_phrases = []
            for i in range(max(0, len(words) - 2)):
                ph = words[i : i + 3]
                if sum(1 for w in ph if w in STOP_WORDS) >= 2:
                    continue
                src_phrases.append(" ".join(ph))
            src_hits = sum(1 for ph in src_phrases[:8] if ph in src)
            src_word_hits = sum(1 for w in words[:12] if w in src)
            if src_hits >= 1 or src_word_hits >= max(3, min(6, len(words[:12]) // 2)):
                url_supports = True
                break

    # Real-but-irrelevant: claim cites a retrieved URL whose text does NOT
    # support it → contested (this is the topicality backstop for high-rep
    # domains the guard demotes but cannot block).
    if verified_eids and src_seen and not url_supports:
        return "contested", max(score * 0.6, 0.2), verified_eids

    if phrase_hits >= 1 or score >= 0.45:
        return "supported", min(1.0, score + (0.15 if url_supports else 0.0)), verified_eids
    if score >= 0.28 or word_hits >= 4:
        return "contested", score, verified_eids
    return "synthetic", score, verified_eids


@register("devil_advocate_gather")
def devil_advocate_gather(state: ResearchState) -> ResearchState:
    """One-shot negative-evidence search: limits, failures, retractions, critiques."""
    if state.get("devil_advocate_done") or state.get("abort_synthesis"):
        return state

    from src.tools import execute_searches
    from src.rag.pipeline import ingest_documents
    from src.engine.budget import record_tool_calls, sync_cost_from_metrics

    query = state.get("query") or ""
    claims = state.get("claims") or []
    findings = state.get("findings") or []
    core = " ".join(re.findall(r"[a-zA-Z]{4,}", query.lower())[:10])

    counter_queries = [
        f"{core} limitations failure modes critique",
        f"{core} does not work negative results",
        f"{query[:100]} retraction OR confounded OR bias",
    ]
    # Target top claims
    for c in claims[:3]:
        ct = (c.get("text") or "")[:100]
        if ct:
            counter_queries.append(f"{ct[:80]} criticism OR limitation")

    counter_queries = counter_queries[:5]
    state["status"] = "Devil's advocate: searching counter-evidence..."
    _progress("adversary", state["status"])
    print(f"\n⚔️  [Devil's Advocate] {len(counter_queries)} counter-queries")
    try:
        from src.engine.progress import get_progress
        get_progress().think("next", f"Counter-search: {counter_queries[0][:100]}")
    except Exception:
        pass

    results = execute_searches(counter_queries, max_results=6)
    record_tool_calls(state, n=len(counter_queries))
    # Cap and tag
    seen = {r.get("url") for r in (state.get("search_results") or []) if r.get("url")}
    new_hits = []
    for r in results:
        url = r.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        r = dict(r)
        r["source"] = (r.get("source") or "") + "+devil_advocate"
        r["guard_score"] = float(r.get("score") or 0.7)
        new_hits.append(r)

    if new_hits:
        state["search_results"] = list(state.get("search_results") or []) + new_hits[:12]
        pages = []
        for r in new_hits[:8]:
            raw = r.get("raw_content") or r.get("content") or ""
            if raw:
                pages.append({
                    "url": r.get("url", ""),
                    "title": f"[Counter] {r.get('title', '')}",
                    "content": raw[:10000],
                    "source_type": "counter_evidence",
                })
        if pages:
            ingested = ingest_documents(pages, run_id=state.get("run_id", "default"))
            state["chunks_ingested"] = int(state.get("chunks_ingested") or 0) + ingested
            print(f"  Counter-evidence: +{len(new_hits)} hits, ingested {ingested} chunks")
        # Seed findings so synth sees adversarial notes
        titles = [h.get("title", "")[:80] for h in new_hits[:5]]
        state.setdefault("findings", []).append(
            "Devil's advocate sources (limitations/counter): " + "; ".join(titles)
        )
        state.setdefault("gaps", [])
        state["gaps"].append(
            "Counter-evidence gathered — report must address limitations and failed cases"
        )
    else:
        print("  Counter-evidence: no new hits")

    state["devil_advocate_done"] = True
    sync_cost_from_metrics(state)
    return state


@register("claim_adjudicator")
def claim_adjudicator(state: ResearchState) -> ResearchState:
    """CoVe-lite: score claims; optional one Socratic re-gather on contested set."""
    if state.get("abort_synthesis"):
        state["socratic_reopen"] = False
        return state

    claims = list(state.get("claims") or [])
    corpus = _corpus(state)
    # Known-retrieved URL set + per-URL text (only URLs from THIS run count).
    # Claims accumulate across research iterations, so the known set is the union
    # of the cumulative evidence_map (which researcher_analyze already filtered to
    # actually-retrieved URLs) plus the current iteration's retrieval state.
    known_urls: set[str] = set()
    url_text: dict[str, str] = {}
    for u in (state.get("evidence_map") or {}):
        known_urls.add(canonical_url(u))
    for c in state.get("run_corpus") or []:
        u = canonical_url(c.get("url") or "")
        if u:
            known_urls.add(u)
            url_text.setdefault(u, "")
            url_text[u] += " " + (c.get("text") or "")
    for c in state.get("retrieved_chunks") or []:
        u = canonical_url(c.get("url") or "")
        if u:
            known_urls.add(u)
            url_text.setdefault(u, "")
            url_text[u] += " " + (c.get("text") or "")
    for p in state.get("extracted_pages") or []:
        u = canonical_url(p.get("url") or "")
        if u:
            known_urls.add(u)
            url_text.setdefault(u, "")
            url_text[u] += " " + (p.get("content") or "")[:4000]
    for r in state.get("search_results") or []:
        u = canonical_url(r.get("url") or "")
        if u:
            known_urls.add(u)
            url_text.setdefault(u, "")
            url_text[u] += " " + (r.get("raw_content") or r.get("content") or "")[:4000]

    adjudicated = []
    contested = []
    synthetic = []
    supported_n = 0

    for c in claims:
        text = c.get("text") or ""
        eids = c.get("evidence_ids") or []
        status, score, verified_eids = _claim_support(text, corpus, eids, known_urls, url_text)
        row = {
            "text": text[:400],
            "status": status,
            "score": round(score, 3),
            "evidence_ids": verified_eids[:5],
        }
        adjudicated.append(row)
        if status == "supported":
            supported_n += 1
        elif status == "contested":
            contested.append(row)
        else:
            synthetic.append(row)

    state["adjudicated_claims"] = adjudicated
    state["contested_claims"] = contested
    state["synthetic_claims"] = synthetic
    total = max(len(adjudicated), 1)
    print(
        f"\n⚖️  [Adjudicator] claims: {supported_n} supported, "
        f"{len(contested)} contested, {len(synthetic)} synthetic "
        f"(of {len(adjudicated)})"
    )

    # Research debt seeds
    debt = list(state.get("research_debt") or [])
    for s in synthetic[:5]:
        debt.append(
            f"Synthetic inference (no solid source chunk): {s['text'][:160]}"
        )
    for c in contested[:5]:
        debt.append(
            f"Contested claim needs stronger evidence: {c['text'][:160]}"
        )
    for g in (state.get("gaps") or [])[:5]:
        debt.append(f"Open gap: {g}"[:220])
    # Dedupe
    seen_d = set()
    clean_debt = []
    for d in debt:
        if d not in seen_d:
            seen_d.add(d)
            clean_debt.append(d)
    state["research_debt"] = clean_debt[:20]

    hops = int(state.get("socratic_hops") or 0)
    max_hops = 1  # Ultra-lite: one Socratic tree expansion
    # Only reopen after devil's advocate has run, and only once
    if (
        (contested or synthetic)
        and hops < max_hops
        and state.get("devil_advocate_done")
        and not state.get("socratic_done")
    ):
        state["socratic_hops"] = hops + 1
        queries = []
        for row in (contested + synthetic)[:4]:
            t = row["text"][:100]
            queries.append(f"{t} evidence empirical study")
            queries.append(f"{t} limitations counterexample")
        q0 = state.get("query") or ""
        queries.append(f"{q0[:80]} systematic review evidence")
        final_q = []
        seen_q: set[str] = set()
        for q in queries:
            ql = q.lower().strip()
            if ql and ql not in seen_q:
                seen_q.add(ql)
                final_q.append(q)
        state["search_queries"] = final_q[:6]
        state["needs_more_research"] = True
        state["socratic_reopen"] = True
        print(f"  Socratic hop {state['socratic_hops']}: re-search {len(state['search_queries'])} queries")
        try:
            from src.engine.progress import get_progress
            get_progress().think("gap", f"{len(contested)} contested + {len(synthetic)} synthetic claims")
            get_progress().think("next", "Socratic re-gather on contested claims")
        except Exception:
            pass
    else:
        state["socratic_reopen"] = False
        state["socratic_done"] = True
        state["needs_more_research"] = False
        if clean_debt and (state.get("mode") or "") in ("deep", "academic", "ultra-long", "standard"):
            try:
                raw = call_llm(
                    "You list remaining research uncertainty. Return JSON only.",
                    f"Query: {state.get('query')}\n"
                    f"Debt notes:\n" + "\n".join(f"- {d}" for d in clean_debt[:12]) + "\n"
                    'Return JSON: {"research_debt": ["...", "..."], "confidence_note": "..."}\n'
                    "Max 6 debt bullets; actionable experiments/data still needed.",
                    model="fast",
                    max_tokens=600,
                )
                cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
                if "{" in cleaned:
                    cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
                data = json.loads(cleaned)
                if isinstance(data.get("research_debt"), list) and data["research_debt"]:
                    state["research_debt"] = [str(x)[:240] for x in data["research_debt"][:8]]
                if data.get("confidence_note"):
                    state["confidence_note"] = str(data["confidence_note"])[:400]
            except Exception:
                pass

    try:
        from src.engine.progress import get_progress
        get_progress().update(
            status=f"Adjudication: {supported_n}/{len(adjudicated)} supported",
            findings_count=len(state.get("findings") or []),
        )
    except Exception:
        pass
    state["status"] = (
        f"Adjudication: {supported_n} supported / {len(contested)} contested / "
        f"{len(synthetic)} synthetic"
    )
    return state
