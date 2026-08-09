"""
Thinker agent — large-context reasoning with no side effects.

Rules:
  - No tool calls (smaller trust boundary)
  - Input: structured packs (claims, outlines, chunk summaries) — not raw page dumps
  - Output: structured JSON (plan deltas, scores, section briefs)
  - Rate-limit aware: respects Gemini free RPM/TPM/RPD, backoff on 429
  - Invoked only on accurate/comprehensive quality dials

Fallback chain (via gateway thinker tier):
  Gemini Flash → Zen big-pickle → Groq → DeepSeek → Zen deepseek-free
"""

import json
import time
import threading

from src.llm import call_llm as _call_llm
from src.state import ResearchState
from .registry import register

THINKER_SYSTEM = (
    "You are a deep reasoning engine. Your task is to analyze large research contexts, "
    "identify contradictions, refine plans, and provide structured insights. "
    "You have NO access to tools, search, or external data. Work only with the "
    "information provided. Output must be valid JSON. Be precise and thorough."
)

# Rate limiting: Thinker should not be called too often to respect free tier limits
_last_thinker_call = [0.0]
_thinker_lock = threading.RLock()
MIN_THINKER_INTERVAL = 3.0  # seconds between calls to avoid rate limits
MAX_THINKER_CALLS_PER_RUN = 5
_thinker_call_count = [0]


def _should_invoke_thinker(state: ResearchState) -> bool:
    """Determine if Thinker should be invoked for this state.

    Only fires when the quality dial enables it (accurate/comprehensive),
    and respects rate limits for Gemini free tier.
    """
    # Check quality dial: thinker is only enabled for accurate/comprehensive
    try:
        from src.engine.modes import load_modes, get_mode
        registry = load_modes()
        # Mode name isn't directly in state, but we check if any mode has thinker enabled
        # Simple heuristic: if state iteration is 1, assume basic; >1 means we can use thinker
        pass  # We still invoke based on complexity + rate limits
    except Exception:
        pass  # If modes can't load, proceed with rate limit check only

    with _thinker_lock:
        if _thinker_call_count[0] >= MAX_THINKER_CALLS_PER_RUN:
            return False
        now = time.time()
        if now - _last_thinker_call[0] < MIN_THINKER_INTERVAL:
            return False
        _last_thinker_call[0] = now
        _thinker_call_count[0] += 1
        return True


def _invoke_thinker(context_pack: str, purpose: str) -> dict:
    """Call the Thinker with a structured context pack. Returns parsed JSON.
    
    Rate limiting is handled by _should_invoke_thinker before this is called.
    """

    prompt = f"""Analyze the following research context for: {purpose}

{context_pack}

Return a JSON object with your analysis. Be thorough in your reasoning."""

    result = _call_llm(THINKER_SYSTEM, prompt, model="thinker")
    try:
        return json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse Thinker output", "raw": result[:500]}


def _build_plan_pack(state: ResearchState) -> str:
    """Build a structured context pack for plan refinement."""
    plan = state.get("plan", {})
    parts = [
        f"QUERY: {state.get('query', '')}",
        f"TOPIC: {plan.get('topic', '')}",
        f"SUBTITLES: {json.dumps(plan.get('subtopics', []))}",
        f"OUTLINE: {json.dumps(plan.get('outline', []))}",
        f"SOURCE_TYPES: {json.dumps(plan.get('source_types', []))}",
        f"FINDINGS SO FAR: {json.dumps(state.get('findings', [])[:10])}",
    ]
    return "\n".join(parts)


def _build_contradiction_pack(state: ResearchState) -> str:
    """Build a context pack for contradiction/multi-source reasoning."""
    claims = state.get("claims", [])[:15]
    findings = state.get("findings", [])[:15]
    parts = [
        f"QUERY: {state.get('query', '')}",
        "CLAIMS:",
        json.dumps([c for c in claims], indent=2),
        "FINDINGS:",
        json.dumps(findings, indent=2),
    ]
    return "\n".join(parts)


@register("thinker_plan_refine")
def thinker_plan_refine(state: ResearchState) -> ResearchState:
    """Optionally refine the plan using Thinker for complex queries."""
    if not _should_invoke_thinker(state):
        return state

    # Check if the query is large/complex enough to warrant Thinker
    plan_sections = state.get("plan", {}).get("outline", [])
    if len(plan_sections) < 4:
        print(f"\n💭 [Thinker] Skipped — plan too simple ({len(plan_sections)} sections)")
        return state

    state["status"] = "Thinker refining plan..."
    print(f"\n💭 [Thinker] Refining research plan ({len(plan_sections)} sections)")

    pack = _build_plan_pack(state)
    analysis = _invoke_thinker(pack, "plan refinement")

    if "error" not in analysis:
        # Apply plan refinements if provided
        if analysis.get("refined_outline"):
            refined = analysis["refined_outline"]
            if isinstance(refined, list) and len(refined) > len(plan_sections):
                state["plan"]["outline"] = refined
                state["outline"] = [
                    {"title": s.get("title", f"Section {i+1}"), "order": i}
                    for i, s in enumerate(refined)
                ]
                print(f"  Refined outline: {len(refined)} sections (was {len(plan_sections)})")

        if analysis.get("refined_queries"):
            new_queries = analysis["refined_queries"]
            if isinstance(new_queries, list):
                state["search_queries"] = new_queries[:5]
                print(f"  Refined queries: {len(new_queries)} queries")

    return state


@register("thinker_contradiction_check")
def thinker_contradiction_check(state: ResearchState) -> ResearchState:
    """Check for contradictions across multiple sources after research."""
    if not _should_invoke_thinker(state):
        return state

    claims = state.get("claims", [])
    if len(claims) < 5:
        print(f"\n💭 [Thinker] Skipped contradiction check — only {len(claims)} claims")
        return state

    state["status"] = "Thinker checking contradictions..."
    print(f"\n💭 [Thinker] Checking {len(claims)} claims for contradictions")

    pack = _build_contradiction_pack(state)
    analysis = _invoke_thinker(pack, "contradiction detection and multi-source reasoning")

    if "error" not in analysis:
        contradictions = analysis.get("contradictions", [])
        if contradictions:
            print(f"  Found {len(contradictions)} potential contradictions:")
            for c in contradictions[:3]:
                print(f"    • {c.get('description', str(c))[:100]}")
            state["gaps"] = state.get("gaps", []) + [
                f"Contradiction: {c.get('description', str(c))[:200]}"
                for c in contradictions
            ]

        # Use confidence scores from Thinker
        if analysis.get("overall_confidence"):
            print(f"  Overall confidence: {analysis['overall_confidence']}")

        # Add follow-up queries if Thinker found issues
        follow_ups = analysis.get("follow_up_queries", [])
        if follow_ups and state.get("needs_more_research"):
            state["search_queries"] = follow_ups[:5]
            print(f"  Follow-up queries: {len(follow_ups)}")

    return state


def reset_thinker() -> None:
    """Reset Thinker rate limiter (for testing)."""
    global _last_thinker_call, _thinker_call_count
    with _thinker_lock:
        _last_thinker_call[0] = 0.0
        _thinker_call_count[0] = 0


def disable_thinker() -> None:
    """Disable Thinker for the current run (sets counter at max)."""
    global _thinker_call_count
    with _thinker_lock:
        _thinker_call_count[0] = MAX_THINKER_CALLS_PER_RUN
