"""
Vault — persistent cross-run source storage.

Saves all search results, extracted pages, and quality scores to disk
for reuse across research runs. Before making paid API calls, the vault
is checked for recent, high-quality sources on similar queries.

Storage: SQLite database at data/vault.db (auto-created).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Optional


class Vault:
    """Persistent, searchable archive of research sources across runs."""

    def __init__(self, db_path: str = "") -> None:
        if not db_path:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "data", "vault.db",
            )
        self.db_path = os.path.abspath(db_path)
        self._lock = threading.RLock()
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _ensure_schema(self) -> None:
        with self._lock:
            conn = self._conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT DEFAULT '',
                    snippet TEXT DEFAULT '',
                    domain TEXT DEFAULT '',
                    source_type TEXT DEFAULT 'web',
                    quality_score REAL DEFAULT 5.0,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    seen_count INTEGER DEFAULT 1,
                    topics TEXT DEFAULT '[]',
                    search_queries TEXT DEFAULT '[]'
                );
                CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
                CREATE INDEX IF NOT EXISTS idx_sources_quality ON sources(quality_score);
                CREATE INDEX IF NOT EXISTS idx_sources_last_seen ON sources(last_seen);
            """)
            conn.commit()
            conn.close()

    def store_results(
        self,
        results: list[dict],
        queries: Optional[list[str]] = None,
    ) -> int:
        """Store search results in the vault.

        Args:
            results: List of search result dicts with {url, title, content/snippet}.
            queries: Search queries that produced these results (for topic tracking).

        Returns:
            Number of new sources stored.
        """
        if not results:
            return 0

        now = time.time()
        queries_json = json.dumps(queries or [])

        with self._lock:
            conn = self._conn()
            new_count = 0
            for r in results:
                url = r.get("url", "")
                if not url:
                    continue

                title = r.get("title", "")
                snippet = (r.get("content", "") or r.get("snippet", "") or "")[:1000]
                domain = self._extract_domain(url)
                quality = float(r.get("guard_score", r.get("score", 5.0)))

                # Generate topic tags from snippet
                topics = json.dumps(self._extract_topics(snippet, title))

                # Upsert: insert or update
                existing = conn.execute(
                    "SELECT id, seen_count, search_queries FROM sources WHERE url = ?",
                    (url,),
                ).fetchone()

                if existing:
                    existing_queries = json.loads(existing[2] or "[]")
                    merged_queries = list(set(existing_queries + (queries or [])))
                    conn.execute(
                        """UPDATE sources SET
                            title = ?, snippet = ?, quality_score = ?,
                            last_seen = ?, seen_count = seen_count + 1,
                            topics = ?, search_queries = ?
                           WHERE url = ?""",
                        (title, snippet, quality, now, topics,
                         json.dumps(merged_queries), url),
                    )
                else:
                    conn.execute(
                        """INSERT INTO sources
                           (url, title, snippet, domain, quality_score,
                            first_seen, last_seen, topics, search_queries)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (url, title, snippet, domain, quality,
                         now, now, topics, queries_json),
                    )
                    new_count += 1

            conn.commit()
            conn.close()
            return new_count

    def search(
        self,
        query: str,
        k: int = 10,
        min_quality: float = 3.0,
        max_age_days: float = 90.0,
    ) -> list[dict]:
        """Search the vault for sources matching a query.

        Uses SQLite FTS on snippet + title, ranked by quality and recency.

        Args:
            query: Search query.
            k: Max results.
            min_quality: Minimum quality_score (0-10).
            max_age_days: Only include sources seen within this many days.

        Returns:
            List of {url, title, snippet, domain, quality_score, last_seen}.
        """
        with self._lock:
            conn = self._conn()
            cutoff = time.time() - max_age_days * 86400

            # Simple keyword search on snippet + title
            keywords = query.lower().split()
            conditions = []
            params: list = []
            for kw in keywords[:5]:
                if len(kw) > 2:
                    conditions.append(
                        "(snippet LIKE ? OR title LIKE ?)"
                    )
                    params.extend([f"%{kw}%", f"%{kw}%"])

            if not conditions:
                conn.close()
                return []

            where = " AND ".join(conditions)
            sql = f"""
                SELECT url, title, snippet, domain, quality_score, last_seen,
                       seen_count
                FROM sources
                WHERE ({where})
                  AND quality_score >= ?
                  AND last_seen >= ?
                ORDER BY quality_score DESC, last_seen DESC
                LIMIT ?
            """
            params.extend([min_quality, cutoff, k])

            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                conn.close()
                return []

            conn.close()
            return [
                {
                    "url": r[0], "title": r[1], "snippet": r[2],
                    "domain": r[3], "quality_score": r[4],
                    "last_seen": r[5], "seen_count": r[6],
                }
                for r in rows
            ]

    def stats(self) -> dict:
        """Return vault statistics."""
        with self._lock:
            conn = self._conn()
            total = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            domains = conn.execute(
                "SELECT COUNT(DISTINCT domain) FROM sources"
            ).fetchone()[0]
            avg_quality = conn.execute(
                "SELECT AVG(quality_score) FROM sources"
            ).fetchone()[0] or 0
            conn.close()
            return {
                "total_sources": total,
                "unique_domains": domains,
                "avg_quality": round(avg_quality, 1),
            }

    @staticmethod
    def _extract_domain(url: str) -> str:
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    @staticmethod
    def _extract_topics(snippet: str, title: str) -> list[str]:
        """Extract simple topic keywords from snippet+title."""
        text = f"{title} {snippet}".lower()
        # Common topic words (simple heuristic)
        topic_words = {
            "ai", "ml", "quantum", "research", "study", "paper",
            "algorithm", "model", "data", "science", "engineering",
            "medicine", "climate", "energy", "space", "biology",
            "physics", "chemistry", "math", "computer", "network",
            "security", "privacy", "blockchain", "crypto", "web",
            "mobile", "cloud", "server", "database", "linux",
        }
        return [w for w in topic_words if w in text][:10]
