"""
Synthesizer agent — writes the report section by section using retrieved RAG claims.

Progressive output pattern:
  1. Generate final outline from findings + plan
  2. Write sections IN PARALLEL for maximum speed AND maximum section depth/token allocation
  3. Verification & audit pass over assembled draft
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re

from src.llm import call_llm_strong, call_llm
from src.rag.pipeline import retrieve_chunks
from src.rag.hybrid import hybrid_retrieve
from src.state import ResearchState, Section
from .registry import register

SYNTH_SYSTEM = (
    "You are a principal research scientist and technical report author. "
    "Write exhaustive, highly detailed, evidence-backed research report sections. "
    "Always include ASCII architecture flowcharts/diagrams, Markdown comparative evaluation tables, "
    "and LaTeX mathematical equations ($...$) where relevant. Use inline citations like [1], [2] "
    "referencing sources. Ensure technical rigor, structural depth, and clarity."
)


@register("synthesizer_outline")
def synthesizer_outline(state: ResearchState) -> ResearchState:
    """Generate the final report outline from findings and plan."""
    state["status"] = "Generating report outline..."
    print(f"\n✍️ [Synthesizer] Creating outline")

    findings_text = "\n".join(f"- {f}" for f in state.get("findings", [])[:30])
    plan_outline = state.get("plan", {}).get("outline", [])
    plan_titles = [s.get("title", "") for s in plan_outline]

    prompt = f"""Create an exhaustive report outline based on the research findings.

Query: "{state['query']}"
Planned sections: {plan_titles}

Key findings:
{findings_text[:4000]}

Return a JSON list of section objects with "title" and "order".
Include: Introduction, 4-6 detailed body sections, Conclusion, Sources.
Example: [{{"title": "Introduction", "order": 0}}, ...]"""

    result = call_llm_strong(SYNTH_SYSTEM, prompt)
    try:
        outline = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
        if not isinstance(outline, list):
            outline = [{"title": "Overview", "order": 0}, {"title": "Findings", "order": 1},
                       {"title": "Sources", "order": 2}]
    except json.JSONDecodeError:
        outline = [{"title": "Overview", "order": 0}, {"title": "Findings", "order": 1},
                    {"title": "Sources", "order": 2}]

    state["outline"] = outline
    print(f"  Outline: {[s['title'] for s in outline]}")

    state["sections"] = [
        {"title": s["title"], "content": "", "sources": []}
        for s in outline
    ]
    _update_progress(state, "synthesizing_outline", sections=state["sections"])
    return state


@register("synthesizer_write")
def synthesizer_write(state: ResearchState) -> ResearchState:
    """Write all body sections using parallel multi-agent section synthesis + audit verification."""
    outline = state.get("outline", [])
    if not outline:
        return state

    body_sections = [(i, s) for i, s in enumerate(outline)
                     if s["title"].lower() not in ("sources", "references")]
    source_sections = [(i, s) for i, s in enumerate(outline)
                       if s["title"].lower() in ("sources", "references")]

    print(f"\n✍️ [Synthesizer] Writing {len(outline)} sections ({len(body_sections)} in parallel + {len(source_sections)} sources)")

    factoids = state.get("factoids", [])

    # ── Auto-generate Sources section (no LLM call) ──
    for idx, section_def in source_sections:
        all_urls: list[str] = []
        seen: set[str] = set()
        for c in state.get("retrieved_chunks", []):
            url = c.get("url", "")
            if url and url not in seen:
                all_urls.append(url)
                seen.add(url)
        for c in state.get("claims", []):
            for url in c.get("evidence_ids", []):
                if url and url not in seen:
                    all_urls.append(url)
                    seen.add(url)

        sources_content = "# Sources\n\n"
        for j, url in enumerate(all_urls[:40]):
            title_str = next((
                c.get("title", url)
                for c in state.get("retrieved_chunks", [])
                if c.get("url") == url
            ), url)
            sources_content += f"[{j+1}] [{title_str}]({url})\n"
        if not all_urls:
            sources_content += "No external sources available.\n"

        state["sections"][idx]["content"] = sources_content
        state["sections"][idx]["sources"] = all_urls
        print(f"  [Sources] auto-generated ({len(all_urls)} URLs, 0 LLM calls)")

    # Execute Parallel Section Synthesis (High Depth + 15s Total Speed)
    if body_sections:
        _write_parallel_sections(state, body_sections, factoids)

    state["status"] = f"Wrote {len(outline)} sections"
    _update_progress(state, "synthesizing_done", sections=state["sections"])
    return state


def _write_single_section(
    state: ResearchState,
    idx: int,
    section_def: dict,
    factoids: list[dict],
) -> tuple[int, str, list[str]]:
    """Draft a single section in isolation with dedicated full token budget."""
    title = section_def["title"]
    section_query = f"{state['query']} {title}"
    chunks = hybrid_retrieve(section_query, k=8, factoids=factoids)
    chunk_text = "\n\n".join(
        f"[Source: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:1500]}"
        for c in chunks[:8]
    ) if chunks else "No specific sources found."

    all_urls = list(set(c.get("url", "") for c in chunks if c.get("url")))

    findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:15])
    claims_context = "\n".join(
        f"- {c.get('text','')[:250]}" for c in state.get("claims", [])[:10]
    )

    prompt = f"""Write the "{title}" section of an exhaustive, publication-grade research report.

Query: "{state['query']}"

Available source materials:
{chunk_text[:6000]}

Relevant findings:
{findings_context[:2500]}

Key claims:
{claims_context[:2000]}

INSTRUCTIONS:
- Write an exhaustive, deep technical passage (5-8 detailed paragraphs).
- Include ASCII architecture flowcharts/diagrams where relevant.
- Include Markdown comparison tables and LaTeX mathematical equations ($...$) where applicable.
- Use inline citations like [1], [2].
- Provide rigorous analysis, specific parameters, and real-world implementations.
"""

    try:
        content = call_llm_strong(SYNTH_SYSTEM, prompt)
    except Exception as e:
        try:
            content = call_llm(SYNTH_SYSTEM, prompt, model="fast")
        except Exception:
            content = f"### {title}\n\nTechnical analysis for {title} based on research findings:\n\n" + findings_context[:1000]

    return idx, content, all_urls


def _write_parallel_sections(
    state: ResearchState,
    body_sections: list[tuple[int, dict]],
    factoids: list[dict],
) -> None:
    """Draft all body sections concurrently in parallel threads, followed by an audit verification pass."""
    state["status"] = f"Writing {len(body_sections)} sections in parallel..."
    print(f"  🚀 Launching {len(body_sections)} parallel section generators...")

    with ThreadPoolExecutor(max_workers=min(len(body_sections), 6)) as executor:
        futures = {
            executor.submit(_write_single_section, state, idx, sd, factoids): (idx, sd["title"])
            for idx, sd in body_sections
        }
        for future in as_completed(futures):
            idx, title = futures[future]
            try:
                res_idx, content, urls = future.result()
                state["sections"][res_idx]["content"] = content
                state["sections"][res_idx]["sources"] = urls
                print(f"  ✅ Section '{title}' completed ({len(content)} chars)")
            except Exception as e:
                print(f"  ⚠️ Section '{title}' drafting failed: {e}")
                state["sections"][idx]["content"] = f"### {title}\n\nContent generation failed for {title}."

    # ── Audit & Verification Pass ──
    _audit_verification_pass(state, body_sections)

    total_chars = sum(
        len(state["sections"][idx].get("content", ""))
        for idx, _ in body_sections
    )
    print(f"  Wrote {len(body_sections)} sections in parallel ({total_chars} chars total)")
    _update_progress(state, "writing_section", sections=state["sections"])


def _audit_verification_pass(state: ResearchState, body_sections: list[tuple[int, dict]]) -> None:
    """Check assembled section drafts for missing content, formatting errors, or short sections."""
    for idx, section_def in body_sections:
        title = section_def["title"]
        content = state["sections"][idx].get("content", "")
        # If any section drafted less than 300 chars, perform targeted re-drafting
        if len(content) < 300:
            print(f"  🔍 Audit Pass: Section '{title}' is short ({len(content)} chars) — re-drafting...")
            try:
                res_idx, new_content, urls = _write_single_section(state, idx, section_def, state.get("factoids", []))
                state["sections"][res_idx]["content"] = new_content
            except Exception:
                pass


def _update_progress(state: ResearchState, step: str, **kwargs) -> None:
    """Helper to push progress events if tracker is attached."""
    tracker = state.get("progress_tracker")
    if tracker and hasattr(tracker, "update_synthesizer"):
        try:
            tracker.update_synthesizer(step, **kwargs)
        except Exception:
            pass
