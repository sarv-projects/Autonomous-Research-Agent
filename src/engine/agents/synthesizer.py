"""
Synthesizer agent — writes the report section by section using retrieved RAG claims.

Progressive output pattern:
  1. Generate final outline from findings + plan
  2. For each section: retrieve relevant chunks → draft section with ASCII diagrams & tables
  3. Stream each section as it's written
"""

import json
import re

from src.llm import call_llm_strong
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
    """Write all body sections using rich contextual retrieval."""
    outline = state.get("outline", [])
    if not outline:
        return state

    body_sections = [(i, s) for i, s in enumerate(outline)
                     if s["title"].lower() not in ("sources", "references")]
    source_sections = [(i, s) for i, s in enumerate(outline)
                       if s["title"].lower() in ("sources", "references")]

    print(f"\n✍️ [Synthesizer] Writing {len(outline)} sections (batched: {len(body_sections)} body + {len(source_sections)} sources)")

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

    mode_name = state.get("mode", "standard")
    use_batched = mode_name in ("quick", "chat")

    if body_sections:
        if use_batched:
            _write_batched(state, body_sections, factoids)
        else:
            _write_per_section(state, body_sections, factoids)

    state["status"] = f"Wrote {len(outline)} sections"
    _update_progress(state, "synthesizing_done", sections=state["sections"])
    return state


def _write_batched(
    state: ResearchState,
    body_sections: list[tuple[int, dict]],
    factoids: list[dict],
) -> None:
    """Write body sections in ONE batched LLM call."""
    state["status"] = "Writing report sections (batched)..."

    all_chunks: list[dict] = []
    for _, sd in body_sections:
        section_query = f"{state['query']} {sd['title']}"
        chunks = hybrid_retrieve(section_query, k=8, factoids=factoids)
        all_chunks.extend(chunks[:8])

    seen_urls: set[str] = set()
    unique_chunks: list[dict] = []
    for c in all_chunks:
        url = c.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_chunks.append(c)

    chunk_text = "\n\n".join(
        f"[Source {j+1}: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:1500]}"
        for j, c in enumerate(unique_chunks[:25])
    ) if unique_chunks else "No specific sources found."

    findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:25])
    claims_context = "\n".join(
        f"- {c.get('text','')[:250]}" for c in state.get("claims", [])[:15]
    )

    section_list = "\n".join(
        f"{i+1}. {sd['title']}" for i, (_, sd) in enumerate(body_sections)
    )

    prompt = f"""Write ALL of the following sections of an exhaustive research report in order.

Query: "{state['query']}"

SECTIONS TO WRITE:
{section_list}

Available source materials:
{chunk_text[:12000]}

Relevant findings:
{findings_context[:3000]}

Key claims:
{claims_context[:2500]}

INSTRUCTIONS:
- Write each section as an exhaustive, highly detailed passage (4-6 comprehensive paragraphs each).
- Include ASCII architecture flowcharts, Markdown comparative analysis tables, and LaTeX equations ($...$) where applicable.
- Use inline citations like [1], [2].
- Separate sections with the exact marker: ===SECTION=== followed by the section title.
"""

    full_text = call_llm_strong(SYNTH_SYSTEM, prompt)

    section_blocks = full_text.split("===SECTION===")
    parsed: dict[str, str] = {}
    for block in section_blocks[1:]:
        lines = block.strip().split("\n", 1)
        if len(lines) >= 2:
            parsed[lines[0].strip().lower()] = lines[1].strip()
        elif lines:
            parsed[lines[0].strip().lower()] = ""

    if not parsed and body_sections:
        first_idx, first_sd = body_sections[0]
        parsed[first_sd["title"].lower()] = full_text

    for idx, section_def in body_sections:
        key = section_def["title"].lower()
        content = parsed.get(key, "")
        if not content:
            for pk, pc in parsed.items():
                if key in pk or pk in key:
                    content = pc
                    break
        if not content:
            content = f"Content for {section_def['title']} could not be parsed."
        state["sections"][idx]["content"] = content
        section_urls = list(set(c.get("url", "") for c in unique_chunks if c.get("url")))
        state["sections"][idx]["sources"] = section_urls

    total_chars = sum(
        len(state["sections"][idx].get("content", ""))
        for idx, _ in body_sections
    )
    print(f"  Wrote {len(body_sections)} sections ({total_chars} chars total)")
    _update_progress(state, "writing_section", sections=state["sections"])


def _write_per_section(
    state: ResearchState,
    body_sections: list[tuple[int, dict]],
    factoids: list[dict],
) -> None:
    """Write each section individually for maximum depth and quality."""
    for i, (idx, section_def) in enumerate(body_sections):
        title = section_def["title"]
        state["status"] = f"Writing section: {title}"

        _update_progress(state, "writing_section",
                         current_section=title, section_index=i + 1,
                         total_sections=len(body_sections),
                         findings_count=len(state.get("findings", [])),
                         factoids_count=len(factoids))

        print(f"  [{i+1}/{len(body_sections)}] {title}...", end=" ", flush=True)

        section_query = f"{state['query']} {title}"
        chunks = hybrid_retrieve(section_query, k=10, factoids=factoids)
        chunk_text = "\n\n".join(
            f"[Source: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:1500]}"
            for c in chunks[:10]
        ) if chunks else "No specific sources found."

        all_urls = list(set(c.get("url", "") for c in chunks if c.get("url")))

        findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:20])
        claims_context = "\n".join(
            f"- {c.get('text','')[:250]}" for c in state.get("claims", [])[:15]
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
- Write an exhaustive, deep technical passage (5-8 paragraphs).
- Include ASCII architecture flowcharts/diagrams where relevant.
- Include Markdown comparison tables and LaTeX mathematical equations ($...$) where applicable.
- Use inline citations like [1], [2].
- Provide rigorous analysis, specific parameters, and real-world implementations.
"""

        content = call_llm_strong(SYNTH_SYSTEM, prompt)
        state["sections"][idx]["content"] = content
        state["sections"][idx]["sources"] = all_urls
        print(f"({len(content)} chars)")
        _update_progress(state, "writing_section", sections=state["sections"])


def _update_progress(state: ResearchState, step: str, **kwargs) -> None:
    """Helper to push progress events if tracker is attached."""
    tracker = state.get("progress_tracker")
    if tracker and hasattr(tracker, "update_synthesizer"):
        try:
            tracker.update_synthesizer(step, **kwargs)
        except Exception:
            pass
