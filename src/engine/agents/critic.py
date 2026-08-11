"""
Critic agent — research quality gate + off-topic hard fail + re-plan signals.

After critic, graph runs thinker_search_strategy to propose better web queries
when more research is needed.
"""

from __future__ import annotations

import json
import re

from src.llm import call_llm
from src.state import ResearchState
from .registry import register

CRITIC_SYSTEM = (
    "You are a strict research quality evaluator for a Deep Research agent. "
    "Detect off-topic contamination. Prefer evidence-backed findings. "
    "Return valid JSON only."
)


def _topic_keywords(query: str) -> set[str]:
    stop = {
        "the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "how",
        "does", "what", "with", "as", "by", "is", "are", "be", "from", "that",
        "this", "into", "about", "cover", "methods", "best", "practices",
    }
    words = re.findall(r"[a-zA-Z]{3,}", query.lower())
    return {w for w in words if w not in stop}


def _findings_on_topic(query: str, findings: list[str]) -> tuple[bool, float]:
    """Heuristic: fraction of findings that share topic keywords with query."""
    kws = _topic_keywords(query)
    if not findings or not kws:
        return True, 1.0
    hits = 0
    for f in findings:
        fl = f.lower()
        if sum(1 for k in kws if k in fl) >= min(2, len(kws)):
            hits += 1
    ratio = hits / max(len(findings), 1)
    # Off-topic if almost no findings match core query terms
    return ratio >= 0.25, ratio


@register("critic")
def critic(state: ResearchState) -> ResearchState:
    """Evaluate research completeness; hard-fail off-topic junk."""
    from src.engine.budget import check_budgets, force_complete, sync_cost_from_metrics

    sync_cost_from_metrics(state)
    ok, reason = check_budgets(state)
    if not ok:
        print(f"\n🔎 [Critic] Budget force-complete: {reason}")
        return force_complete(state, reason)

    max_iter = state.get("max_iterations", 6)
    iteration = int(state.get("iteration") or 0)
    findings = list(state.get("findings") or [])
    gaps = list(state.get("gaps") or [])
    query = state.get("query", "")

    state["status"] = f"Evaluating research ({iteration}/{max_iter})..."
    try:
        from src.engine.progress import get_progress
        p = get_progress()
        p.update(
            stage="evaluating",
            status=state["status"],
            iteration=iteration,
            findings_count=len(findings),
            sources_count=len(state.get("evidence_map") or {}),
        )
        p.think("next", "Critic reviewing findings vs query")
    except Exception:
        pass
    print(f"\n🔎 [Critic] Evaluating iteration {iteration}/{max_iter}")

    # ── Hard off-topic gate (P0.2) ──
    # Use findings + titles + urls (arxiv.org/abs/… has no topic words in path)
    on_topic, ratio = _findings_on_topic(query, findings)
    urls = list((state.get("evidence_map") or {}).keys())
    query_kws = _topic_keywords(query)
    source_blob_parts: list[str] = list(urls)
    for c in state.get("retrieved_chunks") or []:
        source_blob_parts.append(str(c.get("title") or ""))
        source_blob_parts.append(str(c.get("url") or ""))
        source_blob_parts.append(str(c.get("text") or "")[:400])
    for r in state.get("search_results") or []:
        source_blob_parts.append(str(r.get("title") or ""))
        source_blob_parts.append(str(r.get("url") or ""))
    source_blob = " ".join(source_blob_parts).lower()
    url_hits = sum(1 for k in query_kws if k in source_blob)
    # Need a few keyword hits across corpus, not just bare URL paths
    sources_on_topic = url_hits >= min(2, max(1, len(query_kws) // 4)) or not (
        urls or state.get("retrieved_chunks") or state.get("search_results")
    )

    # Only hard-fail when findings are clearly off AND sources also look wrong
    hard_off_topic = bool(findings) and (not on_topic) and (not sources_on_topic)
    soft_off_topic = bool(findings) and (not on_topic) and sources_on_topic
    if hard_off_topic:
        print(f"  ⛔ Off-topic detected (findings_ratio={ratio:.2f}, source_kw_hits={url_hits})")
        state["off_topic"] = True
        state["needs_more_research"] = True
        state["replan"] = True
        # Drop contaminated findings so synthesizer cannot use them
        state["findings"] = [f for f in findings if _findings_on_topic(query, [f])[0]]
        state["claims"] = []
        core = " ".join(list(query_kws)[:8])
        state["search_queries"] = [
            f"{core} site:arxiv.org",
            f"{query[:120]} mechanisms evaluation production",
            f"{core} survey review 2024 2025 2026",
            f"{core} best practices limitations",
        ]
        try:
            from src.engine.progress import get_progress
            get_progress().update(off_topic=True, next_action="Hard re-search: off-topic contamination")
            get_progress().think("gap", f"Off-topic contamination ratio={ratio:.2f}")
            get_progress().think("next", "Re-search with arXiv + focused queries")
        except Exception:
            pass
        if iteration >= max_iter:
            state["needs_more_research"] = False
            state["abort_synthesis"] = True
            state["error"] = "Research aborted: could not gather on-topic evidence"
            state["status"] = "Aborted: off-topic evidence only"
            print("  🛑 Abort synthesis — max iters with off-topic evidence")
            return state
        state["status"] = "Off-topic — forcing re-search"
        return state

    if soft_off_topic:
        print(f"  ⚠️  Findings weak on topic (ratio={ratio:.2f}) but sources look relevant — continue")
        state["needs_more_research"] = True if iteration < max_iter else False

    state["off_topic"] = False
    findings_text = "\n".join(f"- {f}" for f in findings)
    gaps_text = "\n".join(f"- {g}" for g in gaps)
    outline_titles = [s.get("title", "") for s in state.get("outline", [])]

    prompt = f"""Evaluate if the research is complete enough to write a publication-grade report.

Query: "{query}"
Iteration: {iteration}/{max_iter}
Expected sections: {outline_titles}
Evidence URLs: {len(urls)}
Findings ({len(findings)}):
{findings_text[:3000]}

Gaps:
{gaps_text[:800]}

Return JSON:
  - "complete": true/false
  - "reason": brief explanation
  - "confidence": "high"|"medium"|"low"
  - "off_topic": true if findings are unrelated to the query
  - "replan": true if the research plan/outline itself should change
  - "gap_queries": 2-5 NEW search queries if not complete
  - "learned": 1-3 short bullets of what we now know
  - "missing": 1-3 short bullets of what is still missing
"""

    result = call_llm(CRITIC_SYSTEM, prompt, model="fast")
    try:
        cleaned = result.strip()
        for pfx in ("```json", "```"):
            if cleaned.startswith(pfx):
                cleaned = cleaned[len(pfx):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        evaluation = json.loads(cleaned)
    except json.JSONDecodeError:
        evaluation = {
            "complete": len(findings) >= 5 and len(urls) >= 3,
            "reason": "JSON parse failed — heuristic complete",
            "confidence": "low",
            "gap_queries": [],
            "off_topic": False,
            "replan": False,
        }

    if evaluation.get("off_topic"):
        state["off_topic"] = True
        state["needs_more_research"] = True
        state["replan"] = True
        state["search_queries"] = evaluation.get("gap_queries") or [
            f"{query} site:arxiv.org",
            query,
        ]
        print(f"  ⛔ LLM critic marked off-topic: {evaluation.get('reason')}")
        if iteration >= max_iter:
            # Reconcile the LLM flag (which only sees the LAST iteration's
            # findings) with the deterministic source-topicality signal. If the
            # gathered SOURCES are clearly on-topic, the LLM flag is a weak
            # final draw — complete with the real evidence instead of aborting.
            if sources_on_topic:
                state["off_topic"] = False
                state["needs_more_research"] = False
                state["replan"] = False
                print(
                    "  ✅ Sources on-topic — completing with gathered evidence "
                    "(LLM findings-only flag overridden)"
                )
            else:
                state["needs_more_research"] = False
                state["abort_synthesis"] = True
                state["error"] = "Research aborted: off-topic"
        return state

    is_complete = bool(evaluation.get("complete", False))
    reason = evaluation.get("reason", "")

    if iteration >= max_iter:
        is_complete = True
        reason = f"Reached max iterations ({max_iter})"

    # Need minimum evidence to complete
    if is_complete and len(urls) < 2 and iteration < max_iter:
        is_complete = False
        reason = "Too few evidence URLs — continue search"
        evaluation["gap_queries"] = evaluation.get("gap_queries") or [query]

    state["needs_more_research"] = not is_complete
    state["replan"] = bool(evaluation.get("replan", False))

    if not is_complete:
        next_queries = evaluation.get("gap_queries") or []
        state["search_queries"] = (next_queries or [query])[:6]
        print(f"  🔄 More needed: {reason}")
        print(f"  Next queries: {state['search_queries']}")
    else:
        print(f"  ✅ Complete: {reason}")

    # Thinking panel
    try:
        from src.engine.progress import get_progress
        p = get_progress()
        for item in evaluation.get("learned") or []:
            p.think("learned", str(item))
        for item in evaluation.get("missing") or gaps[:3]:
            p.think("gap", str(item))
        if not is_complete:
            p.think("next", f"Search: {state.get('search_queries', [''])[0][:120]}")
        else:
            p.think("next", "Proceed to triangulation and synthesis")
        p.update(
            status=f"Evaluation: {'complete' if is_complete else 'needs more'}",
            findings_count=len(state.get("findings") or []),
            sources_count=len(state.get("evidence_map") or {}),
        )
    except Exception:
        pass

    state["status"] = f"Evaluation: {'complete' if is_complete else 'needs more'}"
    return state
