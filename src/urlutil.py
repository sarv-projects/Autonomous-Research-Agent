"""Shared URL canonicalization for evidence verification.

Used by the researcher, the claim adjudicator, and the compiler so that all
three layers agree on what counts as the same URL — e.g. arXiv html/pdf
variants of a paper all normalize to the abs/ canonical form.
"""

from __future__ import annotations

import re

_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf|html)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?")


def canonical_url(url: str) -> str:
    """Normalize a URL for identity comparison.

    - strips trailing slash and fragment
    - maps arXiv abs/pdf/html pages to their abs/ canonical form
      (chunks may hold html/2405.07437v1 while the LLM cites abs/2405.07437)
    """
    if not url:
        return ""
    u = (url or "").strip().rstrip("/")
    u = u.split("#")[0]
    m = _ARXIV_RE.search(u.lower())
    if m:
        return f"https://arxiv.org/abs/{m.group(1)}"
    return u
