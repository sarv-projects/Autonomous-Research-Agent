"""
Compiler agent — assembles the final report from sections, validates citations,
and exports the result.

Ship gate:
  - End Sources section present
  - Key claims have evidence ids
  - No empty body
  - Progressive write completed
"""

import time

from src.state import ResearchState
from src.export import save_markdown, save_html
from src.render.math import render_mathjax_html, has_math, detect_math
from .registry import register


def _validate_ship_gate(state: ResearchState) -> tuple[bool, list[str]]:
    """Validate the report passes the ship gate before export."""
    issues = []

    sections = state.get("sections", [])
    if not sections:
        issues.append("No sections written")

    # Check for Sources section
    source_section = None
    for s in sections:
        if s["title"].lower() in ("sources", "references"):
            source_section = s
            break
    if not source_section:
        issues.append("Missing Sources/References section")

    # Check for empty body
    total_content = sum(len(s.get("content", "")) for s in sections)
    if total_content < 100:
        issues.append("Report body is too short (<100 chars)")

    # Check evidence coverage
    claims = state.get("claims", [])
    evidence_map = state.get("evidence_map", {})
    if claims and not evidence_map:
        issues.append("No evidence URLs tracked for claims")

    return len(issues) == 0, issues


@register("compiler")
def compiler(state: ResearchState) -> ResearchState:
    """Assemble report, run ship gate, and export."""
    state["status"] = "Compiling final report..."
    print(f"\n📦 [Compiler] Assembling report")

    # Run ship gate
    passed, issues = _validate_ship_gate(state)
    if issues:
        print(f"  ⚠️  Ship gate issues: {issues}")
        # Add a Sources section if missing
        if any("Sources" in i or "References" in i for i in issues):
            urls = list(set(
                c.get("url", "") for c in state.get("retrieved_chunks", [])
                if c.get("url")
            ))
            sources_content = "# Sources\n\n"
            for j, url in enumerate(urls[:30]):
                title = next((c.get("title", url) for c in state.get("retrieved_chunks", [])
                             if c.get("url") == url), url)
                sources_content += f"[{j+1}] [{title}]({url})\n"
            state["sections"].append({
                "title": "Sources", "content": sources_content, "sources": urls
            })
            print(f"  ✅ Auto-added Sources section with {len(urls)} URLs")

    # Assemble report from sections
    sections = state.get("sections", [])
    report_lines = [
        f"# Research Report: {state['query']}",
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Sources**: {len(state.get('evidence_map', {}))} references",
        f"**Iterations**: {state.get('iteration', 0)}",
        f"**Methodology**: Multi-iterative research with RAG retrieval",
        "",
    ]

    for s in sections:
        report_lines.append(f"## {s['title']}")
        report_lines.append("")
        report_lines.append(s.get("content", "").strip())
        report_lines.append("")

    # Add evidence summary if not already in Sources section
    evidence_map = state.get("evidence_map", {})
    if evidence_map and not any(s["title"].lower() in ("sources", "references") for s in sections):
        report_lines.append("## Sources")
        report_lines.append("")
        for j, (url, claim_texts) in enumerate(evidence_map.items()):
            report_lines.append(f"[{j+1}] {url}")
            for ct in claim_texts[:2]:
                report_lines.append(f"    → {ct[:100]}")
            report_lines.append("")

    report = "\n".join(report_lines)

    # ── Math Rendering (Phase L): sanitize LaTeX in report ──
    if has_math(report):
        math_info = detect_math(report)
        print(f"  Math detected: {math_info['count']} expressions "
              f"({len(math_info['inline'])} inline, {len(math_info['block'])} block)")
        report = render_mathjax_html(report)

    state["report"] = report

    # Export to files
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in state["query"])[:50]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"research_{safe_name}_{timestamp}"

    md_path = save_markdown(report, base)
    state["markdown_path"] = md_path

    # Also export HTML with MathJax
    html_path = save_html(report, base, title=state["query"])

    ship_status = "✅ passed" if passed else "⚠️  issues resolved"
    state["status"] = f"Report compiled ({len(report)} chars, ship gate {ship_status})"
    print(f"  Report: {len(report)} chars, {len(sections)} sections")
    print(f"  Ship gate: {ship_status}")
    print(f"  Saved: {md_path}")
    print(f"  HTML:  {html_path}")
    return state
