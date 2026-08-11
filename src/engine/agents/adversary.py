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


# ── Tier-2 #14: DeepVerifier-style atomic verification ────────────────────
# Decompose contested/synthetic claims into atomic statements, run a FRESH web
# check against the world (not just this run's corpus), and label each with the
# DRA taxonomy: SUPPORTED / REFUTED / AMBIGUOUS / UNVERIFIABLE.

_DRA_LABELS = ("SUPPORTED", "REFUTED", "AMBIGUOUS", "UNVERIFIABLE")
_NEGATION_HINTS = (
    "does not", "do not", "is not", "are not", "not true", "false",
    "incorrect", "wrong", "refute", "refutes", "debunk", "debunks",
    "no evidence", "contradict", "contradicts", "misleading", "myth",
    "unsubstantiated", "lacks support", "fails to",
)


def _decompose_atoms(claim_text: str) -> list[str]:
    """Split a claim into 1-3 atomic statements on conjunctions/punctuation."""
    import re
    parts = re.split(r"(?:;|,|\band\b|\bbut\b|\bwhereas\b|\bhowever\b)", claim_text)
    atoms = [p.strip() for p in parts if len(p.strip().split()) >= 2][:3]
    return atoms or [claim_text.strip()]


def _flag_value_conflicts(state: ResearchState) -> list[str]:
    """DRNOISE-style conflict detection (Tier-2 #14/#17).

    Two claims about the same subject (shared topic words) that carry different
    numeric values are flagged as a contradiction — the "verification inertia"
    failure mode where an agent stops at the plausible-but-wrong answer-like
    document instead of reconciling the evidence chain. Marks the weaker claim
    contested and records a research-debt note.
    """
    import re as _re
    claims = list(state.get("claims") or [])
    if len(claims) < 2:
        return []

    def _subject(c: dict) -> tuple:
        words = _re.findall(r"[a-zA-Z]{4,}", (c.get("text") or "").lower())
        return tuple(sorted(words[:4]))

    def _values(c: dict) -> list[str]:
        return _re.findall(r"\b\d+(?:\.\d+)?\s*(?:%|MW|GHz|GB|TB|GB/s|million|billion)?\b", (c.get("text") or ""))

    flagged: list[str] = []
    groups: dict[tuple, list[int]] = {}
    for i, c in enumerate(claims):
        subj = _subject(c)
        if subj:
            groups.setdefault(subj, []).append(i)

    for subj, idxs in groups.items():
        if len(idxs) < 2:
            continue
        value_map: dict[str, list[int]] = {}
        for i in idxs:
            for v in _values(claims[i]):
                value_map.setdefault(v, []).append(i)
        if len(value_map) < 2:
            continue  # same value across claims — no conflict
        # Conflicting numeric claims on the same subject → flag both
        note = (
            "Value conflict between claims on the same subject "
            f"({', '.join(sorted(value_map.keys())[:4])}): reconcile against primary sources"
        )
        flagged.append(note)
        for i in idxs:
            row = state.get("adjudicated_claims") or []
            if i < len(row) and row[i].get("status") == "supported":
                row[i]["status"] = "contested"
                row[i]["score"] = min(float(row[i].get("score") or 0.5), 0.5)
                state.setdefault("contested_claims", []).append(row[i])
    if flagged:
        debt = list(state.get("research_debt") or [])
        for n in flagged:
            debt.append(f"DRNOISE conflict: {n}")
        state["research_debt"] = debt[:20]
        print(f"  ⚔️  DRNOISE conflict flags: {len(flagged)}")
    return flagged


def _word_hits(words: list[str], evidence_text: str) -> int:
    """Count claim words present in evidence, with light stemming so
    "reduce" matches "reduces"/"reduced"/"reducing" (better recall)."""
    hits = 0
    for w in words[:12]:
        if w in evidence_text:
            hits += 1
            continue
        stem = re.sub(r"(?:es|ed|ing|s)$", "", w)
        if len(stem) >= 4 and stem in evidence_text:
            hits += 1
    return hits


def _dra_label(atom: str, evidence_text: str) -> tuple[str, float]:
    """Label an atom against fresh evidence: SUPPORTED / REFUTED / AMBIGUOUS."""
    words = re.findall(r"[a-zA-Z]{4,}", atom.lower())
    if not words:
        return "UNVERIFIABLE", 0.0
    hits = _word_hits(words, evidence_text)
    ratio = hits / max(len(words[:12]), 1)
    has_negation = any(h in evidence_text for h in _NEGATION_HINTS)
    if ratio >= 0.5:
        if has_negation:
            return "REFUTED", ratio
        return "SUPPORTED", ratio
    if ratio >= 0.2:
        return "AMBIGUOUS", ratio
    return "UNVERIFIABLE", ratio


def atomic_verify_claims(state: ResearchState, max_claims: int = 4) -> None:
    """Fresh-web verification of the weakest claims (bounded, best-effort).

    Only runs when there are contested/synthetic claims, the mode is research-
    grade (deep/academic/standard/ultra-long), and the tool budget has headroom.
    Writes state["atomic_verified"] and feeds REFUTED/AMBIGUOUS into research debt.
    """
    candidates = list(state.get("contested_claims") or []) + list(
        state.get("synthetic_claims") or []
    )
    if not candidates:
        return
    if (state.get("mode") or "") not in ("deep", "academic", "ultra-long", "standard"):
        return
    budgets = state.get("budgets") or {}
    max_tools = int(budgets.get("max_tool_calls") or 0)
    used = int(budgets.get("tool_calls") or 0)
    if max_tools and used >= int(max_tools * 0.8):
        print("  🔬 Atomic verify skipped — tool budget nearly exhausted")
        return

    from src.tools import execute_searches
    from src.engine.budget import record_tool_calls

    verified: list[dict] = []
    print(f"\n🔬 [Atomic Verifier] fresh-web check on {min(len(candidates), max_claims)} weak claims")
    for row in candidates[:max_claims]:
        claim = (row.get("text") or "")[:200]
        if not claim:
            continue
        atoms = _decompose_atoms(claim)
        query = " ".join(atoms[:2])[:120]
        try:
            results = execute_searches([query], max_results=3)
            record_tool_calls(state, n=1, kind="search")
        except Exception as e:
            print(f"  🔬 verify search failed: {e}")
            continue
        evidence_text = " ".join(
            (r.get("content") or r.get("raw_content") or "") for r in results
        ).lower()[:6000]
        evidence_urls = [r.get("url") for r in results if r.get("url")][:3]
        labels = [_dra_label(a, evidence_text) for a in atoms]
        # Aggregate: any REFUTED → REFUTED; else SUPPORTED only if all supported
        if any(l == "REFUTED" for l, _ in labels):
            dra = "REFUTED"
        elif all(l == "SUPPORTED" for l, _ in labels) and labels:
            dra = "SUPPORTED"
        elif any(l == "SUPPORTED" for l, _ in labels):
            dra = "AMBIGUOUS"
        else:
            dra = "UNVERIFIABLE"
        score = round(sum(s for _, s in labels) / max(len(labels), 1), 3)
        verified.append({
            "claim": claim,
            "atoms": atoms,
            "dra_label": dra,
            "score": score,
            "evidence_urls": evidence_urls,
        })
        print(f"  🔬 {dra}: {claim[:70]}")

    state["atomic_verified"] = verified
    # Feed labels into research debt
    debt = list(state.get("research_debt") or [])
    for v in verified:
        if v["dra_label"] == "REFUTED":
            debt.append(f"Atomic verify REFUTED: {v['claim'][:160]}")
        elif v["dra_label"] == "AMBIGUOUS":
            debt.append(f"Atomic verify ambiguous — needs stronger sources: {v['claim'][:140]}")
    seen_d = set()
    clean = []
    for d in debt:
        if d not in seen_d:
            seen_d.add(d)
            clean.append(d)
    state["research_debt"] = clean[:20]


@register("devil_advocate_gather")
def devil_advocate_gather(state: ResearchState) -> ResearchState:
    """One-shot negative-evidence search: limits, failures, retractions, critiques."""
    if state.get("devil_advocate_done") or state.get("abort_synthesis"):
        return state

    from src.tools import execute_searches
    from src.rag.pipeline import ingest_documents
    from src.engine.budget import budget_status_line, record_tool_calls, sync_cost_from_metrics

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
    budget_line = budget_status_line(state)
    state["status"] = "Devil's advocate: searching counter-evidence..."
    _progress("adversary", state["status"])
    print(f"\n⚔️  [Devil's Advocate] {len(counter_queries)} counter-queries "
          f"({budget_line})")
    try:
        from src.engine.progress import get_progress
        get_progress().think("next", f"Counter-search: {counter_queries[0][:100]}")
    except Exception:
        pass

    results = execute_searches(counter_queries, max_results=6)
    record_tool_calls(state, n=len(counter_queries), kind="search")
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
    evidence_graph: list[dict] = []

    for idx, c in enumerate(claims):
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
        # Evidence graph (Argus): claim → evidence edges with relation label.
        # One edge PER verified evidence URL (multi-evidence claims are honest);
        # a claim with no verified evidence gets a single unsupported leaf edge.
        relation = (
            "support"
            if status == "supported"
            else ("contradiction" if status == "contested" else "unsupported")
        )
        for eid in (verified_eids[:5] or [""]):
            evidence_graph.append({
                "claim_id": f"C{idx + 1}",
                "claim": text[:200],
                "evidence_url": eid,
                "relation": relation,
                "score": round(score, 3),
            })

    state["adjudicated_claims"] = adjudicated
    state["contested_claims"] = contested
    state["synthetic_claims"] = synthetic
    state["evidence_graph"] = evidence_graph
    total = max(len(adjudicated), 1)
    print(
        f"\n⚖️  [Adjudicator] claims: {supported_n} supported, "
        f"{len(contested)} contested, {len(synthetic)} synthetic "
        f"(of {len(adjudicated)})"
    )
    print(
        f"  Evidence graph: {len(evidence_graph)} edges "
        f"({supported_n} support, {len(contested)} contradiction, "
        f"{len(synthetic)} unsupported)"
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

    # Tier-2 #14: fresh-web atomic verification of the weakest claims (bounded)
    atomic_verify_claims(state, max_claims=4)

    # DRNOISE-style value-conflict detection (reconcile evidence chains)
    _flag_value_conflicts(state)

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
                    model="thinker",  # Tier-2 #18: debt synthesis is reasoning
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
