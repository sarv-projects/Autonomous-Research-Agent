"""
Retriever Guard — source credibility verification for the RAG pipeline.

Architecture:
  1. Domain Reputation — whitelist/blacklist with TLD and domain-level scoring
  2. Content Freshness — date extraction + staleness penalty
  3. Citation Quality — composite 0-10 score from all signals
  4. 3-tier Retry Pyramid — backoff → provider failover → semantic rephrase

Integration: runs in researcher_gather after search results arrive, before
pages are extracted or ingested. Low-scoring sources are dropped or demoted.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


# ── Domain Reputation Database ──────────────────────────────────────────

# Trusted TLDs — government, education, established orgs
HIGH_TRUST_TLDS = frozenset({
    ".gov", ".edu", ".mil", ".ac.uk", ".gov.uk", ".edu.au",
    ".gov.au", ".gc.ca", ".europa.eu", ".who.int",
})

# Medium-trust TLDs — generally safe but variable
MEDIUM_TRUST_TLDS = frozenset({
    ".org", ".net", ".io", ".dev", ".co.uk", ".org.uk",
})

# Known high-quality domains (peer-reviewed, official, encyclopedia)
HIGH_REPUTATION_DOMAINS = frozenset({
    "wikipedia.org", "en.wikipedia.org", "arxiv.org", "pubmed.ncbi.nlm.nih.gov",
    "scholar.google.com", "doi.org", "ncbi.nlm.nih.gov", "nature.com",
    "science.org", "pnas.org", "royalsociety.org", "ieee.org", "acm.org",
    "mit.edu", "stanford.edu", "harvard.edu", "ox.ac.uk", "cam.ac.uk",
    "europa.eu", "who.int", "un.org", "worldbank.org", "imf.org",
    "github.com", "stackoverflow.com", "docs.python.org",
    "nasa.gov", "nsf.gov", "nih.gov", "cdc.gov", "fda.gov",
})

# Known low-quality domains (SEO spam, content farms, aggregators)
LOW_REPUTATION_DOMAINS = frozenset({
    "medium.com",  # variable, but too many unvetted posts
    "quora.com", "answers.com", "ezinearticles.com", "hubpages.com",
    "articlecity.com", "buzzle.com", "selfgrowth.com", "sooperarticles.com",
    "thousandarticle.com", "articlesbase.com",
    "pinterest.com", "tumblr.com",  # social, not research
    "scribd.com", "slideshare.net",  # document hosts, not authoritative
})

# Content-farm patterns in domains.
# Note: no bare `news` pattern — legitimate newswire domains (news.com.au,
# news.sky.com, …) are whitelisted via NEWSWIRE_DOMAINS below, which is
# checked BEFORE these patterns, so a `news` regex here would be dead weight
# at best and a false-positive risk at worst.
CONTENT_FARM_PATTERNS = [
    r"best\d*", r"top\d*", r"review(s|er)?", r"howto", r"guide(s)?",
    r"tutorial(s)?", r"learn", r"tips", r"tricks?", r"hack(s|ing)?",
    r"free-?online", r"download", r"\bblog\b",
]

# Known tier-1 newswire domains (financial + general press). These must never
# be treated as content farms — they are the rubric's "tier-1 newswire" source
# category (FT, Reuters, Caixin …) and score high-reputation.
NEWSWIRE_DOMAINS = frozenset({
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com",
    "apnews.com", "afp.com", "bbc.com", "bbc.co.uk", "theguardian.com",
    "economist.com", "nikkei.com", "caixin.com", "scmp.com",
    "ftchinese.com", "finance.yahoo.com", "marketwatch.com",
    "businessinsider.com", "thenextweb.com", "techcrunch.com",
    "axios.com", "politico.com", "theverge.com", "arstechnica.com",
    "news.com.au", "smh.com.au", "theage.com.au", "afr.com",
    "timesofindia.indiatimes.com", "indianexpress.com", "thehindu.com",
    "livemint.com", "business-standard.com",
    "economictimes.indiatimes.com", "cnbctv18.com", "moneycontrol.com",
    "xinhuanet.com", "chinadaily.com.cn",
    "globaltimes.cn", "people.com.cn", "cgtn.com", "asahi.com",
    "japantimes.co.jp", "koreaherald.com", "straitstimes.com",
    "channelnewsasia.com", "dailysabah.com", "hurriyetdailynews.com",
    "aljazeera.com", "dw.com", "france24.com", "rfi.fr",
    "lemonde.fr", "elpais.com", "spiegel.de", "zeit.de", "faz.net",
    "folha.uol.com.br", "oglobo.globo.com", "estadao.com.br",
    "nation.africa", "businessdailyafrica.com", "premiumtimesng.com",
    "punchng.com", "theeastafrican.co.ke", "venturesafrica.com",
    "moneyweb.co.za", "businesslive.co.za", "firstpost.com",
    "ndtv.com", "zeenews.india.com", "gulfnews.com", "khaleejtimes.com",
})


def _extract_domain(url: str) -> str:
    """Extract the registrable domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove port
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain
    except Exception:
        return ""


# Pre-sorted TLDs for longest-match-first (computed at module load)
_HIGH_TRUST_TLDS_SORTED = sorted(HIGH_TRUST_TLDS, key=len, reverse=True)
_MEDIUM_TRUST_TLDS_SORTED = sorted(MEDIUM_TRUST_TLDS, key=len, reverse=True)


def _tld_match(domain: str, tld_set: frozenset[str]) -> bool:
    """Check if domain ends with any TLD from the set."""
    sorted_tlds = _HIGH_TRUST_TLDS_SORTED if tld_set is HIGH_TRUST_TLDS else _MEDIUM_TRUST_TLDS_SORTED
    for tld in sorted_tlds:
        if domain.endswith(tld):
            return True
    return False


def domain_reputation_score(domain: str) -> float:
    """Score a domain's reputation from 0.0 (worst) to 10.0 (best).

    Scoring logic:
      - High-reputation domain → 9.0-10.0
      - High-trust TLD → 7.0-8.0
      - Medium-trust TLD → 5.0-6.0
      - Low-reputation domain → 1.0-2.0
      - Content-farm pattern → 2.0-3.0
      - Otherwise → 4.0-5.0 (neutral)
    """
    if not domain:
        return 4.0

    # Check known reputations first
    if domain in HIGH_REPUTATION_DOMAINS or any(
        domain.endswith("." + hd) for hd in HIGH_REPUTATION_DOMAINS
    ):
        return 9.5

    if domain in NEWSWIRE_DOMAINS or any(
        domain.endswith("." + nd) for nd in NEWSWIRE_DOMAINS
    ):
        return 8.5

    if domain in LOW_REPUTATION_DOMAINS or any(
        domain.endswith("." + ld) for ld in LOW_REPUTATION_DOMAINS
    ):
        return 1.5

    # Check content farm patterns
    domain_base = domain.split(".")[0]
    for pattern in CONTENT_FARM_PATTERNS:
        if re.search(pattern, domain_base, re.IGNORECASE):
            return 2.5

    # TLD-based scoring
    if _tld_match(domain, HIGH_TRUST_TLDS):
        return 7.5
    if _tld_match(domain, MEDIUM_TRUST_TLDS):
        return 5.5

    # Default neutral
    return 4.5


# ── Content Freshness ───────────────────────────────────────────────────

# Date patterns: year-month-day, month-year, just year
DATE_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2})",           # 2024-08-15
    r"(\d{2}/\d{2}/\d{4})",            # 08/15/2024
    r"(\d{4})",                         # 2024 (fallback)
    r"(?:published|updated|posted)[\s:]+(\d{4}-\d{2}-\d{2})",  # published: 2024-08-15
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(\d{4})",
]


def _extract_year(text: str) -> Optional[int]:
    """Extract the most recent publication year mentioned in text.

    Only matches years in the range 1990–current_year+1 to avoid
    false positives from statistics and other 4-digit numbers.
    """
    import datetime
    current_year = datetime.datetime.now().year
    best_year = None

    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # match might be a string (single group) or tuple (multiple groups)
            year_str = match if isinstance(match, str) else match[-1]
            try:
                year = int(year_str)
                if 1990 <= year <= current_year + 1:
                    if best_year is None or year > best_year:
                        best_year = year
            except (ValueError, IndexError):
                continue

    return best_year


def freshness_score(year: Optional[int], max_age_years: int = 5) -> float:
    """Score content freshness from 0.0 (stale) to 10.0 (fresh).

    Args:
        year: Publication/update year, or None if unknown.
        max_age_years: Years after which content scores 0.
    """
    if year is None:
        return 5.0  # Unknown — neutral

    import datetime
    current_year = datetime.datetime.now().year
    age = current_year - year

    if age <= 0:
        return 10.0  # Current/future year
    if age >= max_age_years:
        return 0.0   # Too old

    # Linear decay: 10.0 → 0.0 over max_age_years
    return 10.0 * (1 - age / max_age_years)


# ── Citation Quality Composite ──────────────────────────────────────────

@dataclass
class SourceAssessment:
    """Result of source credibility evaluation."""
    url: str
    domain: str
    title: str = ""

    # Sub-scores (0-10)
    reputation: float = 4.5
    freshness: float = 5.0
    authority_signals: float = 0.0  # bonus points for authority signals

    # Composite
    composite_score: float = 0.0

    # Flags
    is_high_quality: bool = False
    is_blocked: bool = False
    block_reason: str = ""

    # Metadata
    year: Optional[int] = None


def _authority_signals(url: str, title: str = "") -> float:
    """Detect authority signals beyond domain reputation.

    Returns bonus score 0-2 based on signals like:
    - PDF links (often more authoritative/final)
    - Academic language patterns in title
    - Official document indicators
    """
    bonus = 0.0

    # Academic paper signals in title
    if any(kw in title.lower() for kw in
           ["abstract", "journal", "proceedings", "doi:", "conference",
            "arxiv:", "preprint", "dissertation", "thesis"]):
        bonus += 1.0

    # Official document signals in title
    if any(kw in title.lower() for kw in
           ["official", "standard", "specification", "rfc", "policy",
            "regulation", "directive", "legislation"]):
        bonus += 0.5

    # PDF indicator — check URL path, not domain
    if url.lower().endswith(".pdf"):
        bonus += 0.3

    return min(bonus, 2.0)


STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "how",
    "does", "what", "with", "as", "by", "is", "are", "be", "from", "that",
    "this", "into", "about", "cover", "methods", "best", "practices", "do",
    "it", "its", "can", "use", "using", "vs", "versus", "their", "there",
})


# Common acronym expansions so topicality survives RAG/LLM-type queries where
# papers spell out the terms ("retrieval-augmented generation", "language models")
_TOPIC_SYNONYMS = {
    "rag": {"rag", "retrieval", "augmented", "generation", "retrieval-augmented"},
    "llm": {"llm", "llms", "language", "model", "models"},
    "gpt": {"gpt", "chatgpt", "transformer"},
    "ai": {"ai", "artificial", "intelligence"},
    "knn": {"knn", "nearest", "neighbor"},
}


def _topic_keywords(query: str) -> set[str]:
    """Extract meaningful topic keywords from the research query (3+ chars)."""
    words = re.findall(r"[a-zA-Z]{3,}", (query or "").lower())
    out: set[str] = set()
    for w in words:
        if w in STOP_WORDS:
            continue
        out.add(w)
        out.update(_TOPIC_SYNONYMS.get(w, set()))
    return out


def _topicality_score(title: str, snippet: str, topic_keywords: set[str]) -> float:
    """Return 0-10 topical relevance of a result to the query's keywords.

    Uses title + snippet overlap. If we have enough text to judge (>=80 chars)
    and the result shares NO keywords with the query, score 0 (off-topic).
    Otherwise score by keyword-hit density, capped at 10.
    """
    if not topic_keywords:
        return 5.0  # nothing to judge against — neutral
    blob = f"{title} {snippet}".lower()
    if len(blob) < 80:
        return 5.0  # not enough text — do not punish
    hits = sum(1 for k in topic_keywords if k in blob)
    if hits == 0:
        return 0.0
    return min(10.0, 4.0 + hits * 2.0)


def assess_source(
    url: str,
    title: str = "",
    snippet: str = "",
    topic: str = "",
) -> SourceAssessment:
    """Evaluate a single source's credibility.

    Args:
        topic: The research query, used to score topical relevance. Pass it so
            real-but-irrelevant pages (e.g. an arXiv paper on teaching Cantonese
            returned for a RAG-hallucination query) get demoted/blocked.

    Returns a SourceAssessment with scores and flags.
    """
    domain = _extract_domain(url)
    assessment = SourceAssessment(url=url, domain=domain, title=title)

    # 1. Domain reputation
    assessment.reputation = domain_reputation_score(domain)

    # 2. Content freshness
    year = _extract_year(snippet or title)
    assessment.year = year
    assessment.freshness = freshness_score(year)

    # 3. Authority signals
    assessment.authority_signals = _authority_signals(url, title)

    # 4. Composite score (0-10)
    # Reputation is most important, freshness and authority are modifiers
    assessment.composite_score = (
        assessment.reputation * 0.6
        + assessment.freshness * 0.25
        + assessment.authority_signals
    )
    assessment.composite_score = min(max(assessment.composite_score, 0.0), 10.0)

    # 5. Topicality (P0.4): demote/block real-but-irrelevant hits
    top = _topicality_score(title, snippet, _topic_keywords(topic))
    if top == 0.0 and (snippet or title):
        if assessment.reputation >= 7.5:
            # High-reputation academic/government domain: demote rather than
            # block — snippets are often too short to judge topicality, and
            # arXiv/ACL papers legitimately spell out terms differently.
            assessment.composite_score = min(assessment.composite_score, 5.5)
        else:
            assessment.composite_score = min(assessment.composite_score, 1.5)
            assessment.is_blocked = True
            assessment.block_reason = "Off-topic: no query keyword overlap in content"
    else:
        # Mild relevance weight — do not let a hot domain carry irrelevant pages
        assessment.composite_score = assessment.composite_score * 0.8 + top * 0.2
        assessment.composite_score = min(max(assessment.composite_score, 0.0), 10.0)

    # 6. Classification
    if assessment.reputation <= 1.5:
        assessment.is_blocked = True
        assessment.block_reason = f"Low-reputation domain: {domain}"
    elif assessment.composite_score >= 6.0:
        assessment.is_high_quality = True

    return assessment


def filter_results(
    results: list[dict],
    min_score: float = 3.0,
    sort_by_score: bool = True,
    topic: str = "",
) -> tuple[list[dict], dict]:
    """Filter and assess search results through the Retriever Guard.

    Args:
        results: List of search result dicts with {url, title, content/snippet}.
        min_score: Minimum composite score to keep a result.
        sort_by_score: If True, return results sorted by score descending.
        topic: The research query — enables topicality blocking of
            real-but-irrelevant results.

    Returns:
        (filtered_results, guard_stats)
    """
    if not results:
        return [], {"total": 0, "passed": 0, "blocked": 0, "avg_score": 0}

    topic_kw = _topic_keywords(topic)
    assessments: list[SourceAssessment] = []
    pass_count = 0
    block_count = 0

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("content", "") or r.get("snippet", "") or r.get("raw_content", "")

        assessment = assess_source(url, title, snippet, topic=topic)
        assessments.append(assessment)

        if assessment.is_blocked:
            block_count += 1
        elif assessment.composite_score >= min_score:
            pass_count += 1

    # Annotate results with scores (mutate in-place)
    for i, r in enumerate(results):
        if i < len(assessments):
            a = assessments[i]
            r["guard_score"] = round(a.composite_score, 1)
            r["guard_reputation"] = round(a.reputation, 1)
            r["guard_freshness"] = round(a.freshness, 1)
            r["guard_domain"] = a.domain
            r["guard_blocked"] = a.is_blocked
            r["guard_reason"] = a.block_reason

    # Filter: drop blocked, drop low-score
    filtered = [
        r for r in results
        if not r.get("guard_blocked") and r.get("guard_score", 0) >= min_score
    ]

    # Sort by score if requested
    if sort_by_score:
        filtered.sort(key=lambda r: r.get("guard_score", 0), reverse=True)

    total_score = sum(a.composite_score for a in assessments)
    avg_score = total_score / len(assessments) if assessments else 0.0

    guard_stats = {
        "total": len(results),
        "passed": len(filtered),
        "blocked": block_count,
        "avg_score": round(avg_score, 1),
        "off_topic_blocked": sum(
            1 for a in assessments if a.block_reason and "Off-topic" in a.block_reason
        ),
        "domains": _domain_summary(assessments),
    }

    return filtered, guard_stats


def _domain_summary(assessments: list[SourceAssessment]) -> dict:
    """Summarize domain stats."""
    blocked_domains = [a.domain for a in assessments if a.is_blocked]
    high_quality = [a.domain for a in assessments if a.is_high_quality]
    return {
        "blocked": list(set(blocked_domains))[:5],
        "high_quality": list(set(high_quality))[:5],
    }


# ── 3-Tier Retry Pyramid ────────────────────────────────────────────────

def retry_pyramid_filter(
    results: list[dict],
    threshold: int = 3,
) -> list[dict]:
    """3-tier retry pyramid: if too few results pass the guard, progressively
    lower the threshold.

    Tier 1: score ≥ 5.0 (strict — only high-quality)
    Tier 2: score ≥ 3.0 (standard — minimum credible)
    Tier 3: score ≥ 1.0 (lenient — block only known spam/farms)
    """
    tiers = [
        (5.0, "strict"),
        (3.0, "standard"),
        (1.0, "lenient"),
    ]

    for min_score, tier_name in tiers:
        filtered, stats = filter_results(results, min_score=min_score)
        if len(filtered) >= threshold or tier_name == "lenient":
            if tier_name != "standard":
                # Only print if we deviated from standard
                pass  # caller can log
            return filtered

    # Fallback: return all non-blocked
    filtered, _ = filter_results(results, min_score=0.0)
    return filtered
