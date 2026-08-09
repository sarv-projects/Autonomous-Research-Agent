"""
SQLite FTS5 full-text search backend.

A lightweight, always-available keyword search fallback when vector embeddings
are unavailable (no API key, no GPU). Uses Python's stdlib sqlite3 module.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Optional


class FTSStore:
    """SQLite FTS5-based keyword search store."""

    def __init__(self, db_path: str = "") -> None:
        if not db_path:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "fts.db"
            )
        self.db_path = os.path.abspath(db_path)
        self._lock = threading.RLock()
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_schema(self) -> None:
        with self._lock:
            conn = self._conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    url TEXT DEFAULT '',
                    title TEXT DEFAULT '',
                    source_type TEXT DEFAULT '',
                    chunk_index INTEGER DEFAULT 0,
                    run_id TEXT DEFAULT ''
                )
            """)
            # FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
                USING fts5(id, text, url, title, content='chunks', content_rowid='rowid')
            """)
            # Triggers to keep FTS in sync
            conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                    INSERT INTO chunks_fts(rowid, id, text, url, title)
                    VALUES (new.rowid, new.id, new.text, new.url, new.title);
                END;
                CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, id, text, url, title)
                    VALUES ('delete', old.rowid, old.id, old.text, old.url, old.title);
                END;
                CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid, id, text, url, title)
                    VALUES ('delete', old.rowid, old.id, old.text, old.url, old.title);
                    INSERT INTO chunks_fts(rowid, id, text, url, title)
                    VALUES (new.rowid, new.id, new.text, new.url, new.title);
                END;
            """)
            conn.commit()
            conn.close()

    def upsert(self, chunks: list) -> None:
        """Insert or replace chunks."""
        if not chunks:
            return
        with self._lock:
            conn = self._conn()
            for c in chunks:
                meta = getattr(c, "metadata", {}) or {}
                conn.execute(
                    """INSERT OR REPLACE INTO chunks (id, text, url, title, source_type, chunk_index, run_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(c.id),
                        str(c.text)[:10000],
                        str(meta.get("url", "")),
                        str(meta.get("title", "")),
                        str(meta.get("source_type", "")),
                        int(meta.get("chunk_index", 0)),
                        str(meta.get("run_id", "")),
                    ),
                )
            conn.commit()
            conn.close()

    def query(self, text: str, k: int = 10) -> list[dict]:
        """Full-text keyword search."""
        with self._lock:
            conn = self._conn()
            # Clean the query for FTS5
            clean = " ".join(text.split())[:200]
            try:
                rows = conn.execute(
                    """SELECT c.id, c.text, c.url, c.title, c.source_type,
                              c.chunk_index, c.run_id, rank
                       FROM chunks_fts f
                       JOIN chunks c ON c.rowid = f.rowid
                       WHERE chunks_fts MATCH ?
                       ORDER BY rank LIMIT ?""",
                    (clean, k),
                ).fetchall()
            except sqlite3.OperationalError:
                # FTS query parse error (special chars) — fall back to LIKE
                like_term = f"%{clean[:50]}%"
                rows = conn.execute(
                    """SELECT id, text, url, title, source_type, chunk_index, run_id, 1.0
                       FROM chunks WHERE text LIKE ? LIMIT ?""",
                    (like_term, k),
                ).fetchall()
            conn.close()

            return [
                {
                    "id": r[0], "text": r[1], "url": r[2], "title": r[3],
                    "source_type": r[4], "chunk_index": r[5], "run_id": r[6],
                    "score": float(r[7]) if len(r) > 7 else 1.0,
                }
                for r in rows
            ]

    def delete_by_run(self, run_id: str) -> None:
        with self._lock:
            conn = self._conn()
            conn.execute("DELETE FROM chunks WHERE run_id = ?", (run_id,))
            conn.commit()
            conn.close()

    def count(self) -> int:
        with self._lock:
            conn = self._conn()
            cnt = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            conn.close()
            return cnt
