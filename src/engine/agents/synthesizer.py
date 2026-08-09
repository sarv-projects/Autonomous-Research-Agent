"""
Synthesizer agent — writes the report section by section using retrieved RAG claims.

Progressive output pattern:
  1. Generate final outline from findings + plan
  2. For each section: retrieve relevant chunks → draft section
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
    "You are a professional research report writer. Write clear, well-structured, "
    "evidence-backed sections. Use inline citations like [1], [2] referencing the "
    "source list. Write in a professional yet accessible tone."
)


@register("synthesizer_outline")
def synthesizer_outline(state: ResearchState) -> ResearchState:
    """Generate the final report outline from findings and plan."""
    state["status"] = "Generating report outline..."
    print(f"\n✍️ [Synthesizer] Creating outline")

    findings_text = "\n".join(f"- {f}" for f in state.get("findings", [])[:20])
    plan_outline = state.get("plan", {}).get("outline", [])
    plan_titles = [s.get("title", "") for s in plan_outline]

    prompt = f"""Create a final report outline based on the research.

Query: "{state['query']}"
Planned sections: {plan_titles}

Key findings:
{findings_text[:2000]}

Return a JSON list of section objects with "title" and "order".
Include: Introduction, 3-5 body sections, Conclusion, Sources.
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

    # Seed sections with empty content
    state["sections"] = [
        {"title": s["title"], "content": "", "sources": []}
        for s in outline
    ]
    # Update progress tracker
    _update_progress(state, "synthesizing_outline", sections=state["sections"])
    return state


@register("synthesizer_write")
def synthesizer_write(state: ResearchState) -> ResearchState:
    """Write all body sections in ONE batched LLM call for speed.

    Sources section is auto-generated (no LLM needed).
    Body sections (Introduction, body, Conclusion) are written together
    in a single LLM call — this cuts N sequential calls to 1, saving ~N×7s.
    """
    outline = state.get("outline", [])
    if not outline:
        return state

    # Split outline into body sections vs Sources
    body_sections = [(i, s) for i, s in enumerate(outline)
                     if s["title"].lower() not in ("sources", "references")]
    source_sections = [(i, s) for i, s in enumerate(outline)
                       if s["title"].lower() in ("sources", "references")]

    print(f"\n✍️ [Synthesizer] Writing {len(outline)} sections (batched: {len(body_sections)} body + {len(source_sections)} sources)")

    factoids = state.get("factoids", [])

    # ── Auto-generate Sources section (no LLM call) ──
    for idx, section_def in source_sections:
        # Collect all URLs from findings + claims + search results
        all_urls: list[str] = []
        seen: set[str] = set()
        for c in state.get("retrieved_chunks", []):
            url = c.get("url", "")
            if url and url not in seen:
                all_urls.append(url)
                seen.add(url)
        # Also collect from claims evidence
        for c in state.get("claims", []):
            for url in c.get("evidence_ids", []):
                if url and url not in seen:
                    all_urls.append(url)
                    seen.add(url)

        sources_content = "# Sources\n\n"
        for j, url in enumerate(all_urls[:30]):
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

    # ── Write body sections: batched for speed or per-section for quality ──
    # Batch in quick/standard modes; per-section in accurate/comprehensive
    mode_name = state.get("mode", "standard")
    use_batched = mode_name in ("quick", "standard", "chat")

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
    """Write all body sections in ONE batched LLM call (fast)."""
    state["status"] = "Writing report sections (batched)..."

    # Retrieve chunks for all body sections at once
    all_chunks: list[dict] = []
    for _, sd in body_sections:
        section_query = f"{state['query']} {sd['title']}"
        chunks = hybrid_retrieve(section_query, k=5, factoids=factoids)
        all_chunks.extend(chunks[:5])

    # Deduplicate chunks
    seen_urls: set[str] = set()
    unique_chunks: list[dict] = []
    for c in all_chunks:
        url = c.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_chunks.append(c)

    chunk_text = "\n\n".join(
        f"[Source {j+1}: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:300]}"
        for j, c in enumerate(unique_chunks[:15])
    ) if unique_chunks else "No specific sources found."

    findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:15])
    claims_context = "\n".join(
        f"- {c.get('text','')[:150]}" for c in state.get("claims", [])[:10]
    )

    section_list = "\n".join(
        f"{i+1}. {sd['title']}" for i, (_, sd) in enumerate(body_sections)
    )

    prompt = f"""Write ALL of the following sections of a research report in order.

Query: "{state['query']}"

SECTIONS TO WRITE:
{section_list}

Available source materials:
{chunk_text[:4000]}

Relevant findings:
{findings_context[:2000]}

Key claims:
{claims_context[:1500]}

INSTRUCTIONS:
- Write each section as a complete, thorough passage (2-4 paragraphs each).
- Use inline citations like [Source 1], [Source 2].
- Be factual, balanced, and professional.
- Separate sections with the exact marker: ===SECTION=== followed by the section title.

Example format:
===SECTION=== Introduction
(introduction text here...)

===SECTION=== Body Section Name
(section text here...)"""

    _update_progress(state, "writing_section",
                     current_section=f"All {len(body_sections)} body sections",
                     section_index=1, total_sections=1,
                     findings_count=len(state.get("findings", [])),
                     factoids_count=len(factoids))

    print(f"  Writing {len(body_sections)} body sections in 1 batched LLM call...", flush=True)
    full_text = call_llm_strong(SYNTH_SYSTEM, prompt)

    # Parse the batched response using ===SECTION=== markers
    section_blocks = re.split(r"===SECTION===\s*", full_text)
    parsed: dict[str, str] = {}
    for block in section_blocks[1:]:
        lines = block.strip().split("\n", 1)
        if len(lines) >= 2:
            parsed[lines[0].strip().lower()] = lines[1].strip()
        elif lines:
            parsed[lines[0].strip().lower()] = ""

    # Fallback: if parsing produced nothing, assign entire output to first body section
    if not parsed and body_sections:
        first_idx, first_sd = body_sections[0]
        parsed[first_sd["title"].lower()] = full_text
        print(f"    ⚠️  No ===SECTION=== markers found — assigning full output to: {first_sd['title']}")

    # Assign content to body sections
    for idx, section_def in body_sections:
        key = section_def["title"].lower()
        content = parsed.get(key, "")
        if not content:
            for pk, pc in parsed.items():
                if key in pk or pk in key:
                    content = pc
                    break
        if not content:
            content = f"Content for {section_def['title']} could not be parsed from batch response."
            print(f"    ⚠️  Could not parse section: {section_def['title']}")
        state["sections"][idx]["content"] = content
        section_urls = list(set(c.get("url", "") for c in unique_chunks if c.get("url")))
        state["sections"][idx]["sources"] = section_urls

    total_chars = sum(
        len(state["sections"][idx].get("content", ""))
        for idx, _ in body_sections
    )
    print(f"  Wrote {len(body_sections)} sections ({total_chars} chars total, 1 LLM call)")
    _update_progress(state, "writing_section", sections=state["sections"])


def _write_per_section(
    state: ResearchState,
    body_sections: list[tuple[int, dict]],
    factoids: list[dict],
) -> None:
    """Write each section individually for maximum quality (accurate/comprehensive modes)."""
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
        chunks = hybrid_retrieve(section_query, k=8, factoids=factoids)
        chunk_text = "\n\n".join(
            f"[Source: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:400]}"
            for c in chunks[:8]
        ) if chunks else "No specific sources found."

        all_urls = list(set(c.get("url", "") for c in chunks if c.get("url")))
        sources_list = "\n".join(f"[{j+1}] {url}" for j, url in enumerate(all_urls[:20]))

        findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:15])
        claims_context = "\n".join(
            f"- {c.get('text','')[:150]}" for c in state.get("claims", [])[:10]
        )

        prompt = f"""Write the "{title}" section of a research report.

Query: "{state['query']}"

Available source materials:
{chunk_text[:3000]}

Relevant findings:
{findings_context[:1500]}

Key claims:
{claims_context[:1000]}

Source list (cite as [1], [2], etc.):
{sources_list[:600]}

Write a thorough, well-structured section. Use inline citations like [1], [2].
Aim for 2-4 paragraphs. Be factual and balanced."""

        section_text = call_llm_strong(SYNTH_SYSTEM, prompt)
        state["sections"][idx]["content"] = section_text
        state["sections"][idx]["sources"] = all_urls
        print(f"({len(section_text)} chars)")

        _update_progress(state, "writing_section", sections=state["sections"])
        state["status"] = "Writing report sections (batched)..."

        # Retrieve chunks for all body sections at once
        all_chunks: list[dict] = []
        for _, sd in body_sections:
            section_query = f"{state['query']} {sd['title']}"
            chunks = hybrid_retrieve(section_query, k=5, factoids=factoids)
            all_chunks.extend(chunks[:5])

        # Deduplicate chunks
        seen_urls: set[str] = set()
        unique_chunks: list[dict] = []
        for c in all_chunks:
            url = c.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_chunks.append(c)

        chunk_text = "\n\n".join(
            f"[Source {j+1}: {c.get('title','') or c.get('url','')}]\n{c.get('text','')[:300]}"
            for j, c in enumerate(unique_chunks[:15])
        ) if unique_chunks else "No specific sources found."

        findings_context = "\n".join(f"- {f}" for f in state.get("findings", [])[:15])
        claims_context = "\n".join(
            f"- {c.get('text','')[:150]}" for c in state.get("claims", [])[:10]
        )

        # Build the section list for the prompt
        section_list = "\n".join(
            f"{i+1}. {sd['title']}" for i, (_, sd) in enumerate(body_sections)
        )

        prompt = f"""Write ALL of the following sections of a research report in order.

Query: "{state['query']}"

SECTIONS TO WRITE:
{section_list}

Available source materials:
{chunk_text[:4000]}

Relevant findings:
{findings_context[:2000]}

Key claims:
{claims_context[:1500]}

INSTRUCTIONS:
- Write each section as a complete, thorough passage (2-4 paragraphs each).
- Use inline citations like [Source 1], [Source 2].
- Be factual, balanced, and professional.
- Separate sections with the exact marker: ===SECTION=== followed by the section title.

Example format:
===SECTION=== Introduction
(introduction text here...)

===SECTION=== Body Section Name
(section text here...)"""

        _update_progress(state, "writing_section",
                         current_section=f"All {len(body_sections)} body sections",
                         section_index=1, total_sections=1,
                         findings_count=len(state.get("findings", [])),
                         factoids_count=len(factoids))

        print(f"  Writing {len(body_sections)} body sections in 1 batched LLM call...", flush=True)
        full_text = call_llm_strong(SYNTH_SYSTEM, prompt)

        # Parse the batched response using ===SECTION=== markers
        section_blocks = re.split(r"===SECTION===\s*", full_text)
        # First block is empty/prefix text, remaining blocks have "Title\nContent"
        parsed: dict[str, str] = {}
        for block in section_blocks[1:]:  # skip leading empty/prefix
            lines = block.strip().split("\n", 1)
            if len(lines) >= 2:
                sec_title = lines[0].strip()
                sec_content = lines[1].strip()
                parsed[sec_title.lower()] = sec_content
            elif lines:
                parsed[lines[0].strip().lower()] = ""

        # Fallback: if parsing produced nothing, assign entire output to first body section
        if not parsed and body_sections:
            first_idx, first_sd = body_sections[0]
            parsed[first_sd["title"].lower()] = full_text
            print(f"    ⚠️  No ===SECTION=== markers found — assigning full output to: {first_sd['title']}")

        # Assign content to body sections
        for idx, section_def in body_sections:
            key = section_def["title"].lower()
            content = parsed.get(key, "")
            if not content:
                # Fallback: look for partial match
                for pk, pc in parsed.items():
                    if key in pk or pk in key:
                        content = pc
                        break
            if not content:
                content = f"Content for {section_def['title']} could not be parsed from batch response."
                print(f"    ⚠️  Could not parse section: {section_def['title']}")
            state["sections"][idx]["content"] = content
            # Collect sources from chunks
            section_urls = list(set(
                c.get("url", "") for c in unique_chunks if c.get("url")
            ))
            state["sections"][idx]["sources"] = section_urls

        total_chars = sum(
            len(state["sections"][idx].get("content", ""))
            for idx, _ in body_sections
        )
        print(f"  Wrote {len(body_sections)} sections ({total_chars} chars total, 1 LLM call)")

        _update_progress(state, "writing_section", sections=state["sections"])

    state["status"] = f"Wrote {len(outline)} sections"
    _update_progress(state, "synthesizing_done", sections=state["sections"])
    return state


def _update_progress(
    state: ResearchState,
    stage: str,
    sections: list[dict] | None = None,
    current_section: str = "",
    section_index: int = -1,
    total_sections: int = -1,
    findings_count: int = -1,
    factoids_count: int = -1,
) -> None:
    """Emit progress update to the shared progress tracker."""
    try:
        from src.engine.progress import get_progress
        p = get_progress()
        p.update(
            stage=stage,
            sections=sections,
            current_section=current_section,
            section_index=section_index,
            total_sections=total_sections,
            findings_count=findings_count,
            factoids_count=factoids_count,
            status=state.get("status", ""),
            iteration=state.get("iteration", 0),
        )
    except Exception:
        pass  # Progress tracking is best-effort
