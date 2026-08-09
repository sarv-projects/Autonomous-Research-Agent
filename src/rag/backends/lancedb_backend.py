"""
LanceDB vector store backend.

LanceDB is an embedded, columnar vector database that stores data on disk.
No server required — runs in-process with zero Docker dependencies.

Collections:
    chunks   — {id, text, vector(1536), metadata_json}
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa


class LanceDBStore:
    """LanceDB-backed vector store for RAG chunks."""

    def __init__(self, db_path: str = "", vector_dim: int = 1536) -> None:
        if not db_path:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "lancedb"
            )
        self.db_path = os.path.abspath(db_path)
        self.vector_dim = vector_dim
        self._db = lancedb.connect(self.db_path)
        self._table_name = "chunks"

    def _ensure_table(self) -> None:
        """Create the chunks table if it doesn't exist."""
        if self._table_name not in self._db.table_names():
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("text", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), self.vector_dim)),
                pa.field("url", pa.string()),
                pa.field("title", pa.string()),
                pa.field("source_type", pa.string()),
                pa.field("chunk_index", pa.int32()),
                pa.field("run_id", pa.string()),
            ])
            self._db.create_table(self._table_name, schema=schema)

    def upsert(self, chunks: list) -> None:
        """Insert or update chunks in the vector store.

        Removes existing chunks with the same IDs before adding to prevent
        duplicates when the same run re-ingests.

        Args:
            chunks: List of objects with: id, text, embedding (list[float]),
                    and optional metadata dict with url, title, source_type, run_id.
        """
        if not chunks:
            return

        self._ensure_table()
        rows = []
        for c in chunks:
            meta = getattr(c, "metadata", {}) or {}
            vec = getattr(c, "embedding", None) or []
            # Ensure vector is float32
            vec_float = [float(v) for v in vec]
            # Pad or truncate to vector_dim
            if len(vec_float) < self.vector_dim:
                vec_float.extend([0.0] * (self.vector_dim - len(vec_float)))
            vec_float = vec_float[:self.vector_dim]
            rows.append({
                "id": str(c.id),
                "text": str(c.text),
                "vector": vec_float,
                "url": str(meta.get("url", "")),
                "title": str(meta.get("title", "")),
                "source_type": str(meta.get("source_type", "")),
                "chunk_index": int(meta.get("chunk_index", 0)),
                "run_id": str(meta.get("run_id", "")),
            })

        table = self._db.open_table(self._table_name)
        # Remove existing chunks with same IDs before inserting
        chunk_ids = [r["id"] for r in rows]
        try:
            id_list = ", ".join(f"'{cid}'" for cid in chunk_ids)
            table.delete(f"id IN ({id_list})")
        except Exception:
            pass
        table.add(rows)

    def query(
        self,
        embedding: list[float],
        k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Query by vector similarity. Returns top-k chunks with scores."""
        if self._table_name not in self._db.table_names():
            return []

        vec = [float(v) for v in embedding]
        table = self._db.open_table(self._table_name)

        try:
            results = table.search(vec).limit(k).to_list()

            # Remove vector from results to keep them light
            return [
                {
                    "id": r.get("id", ""),
                    "text": r.get("text", ""),
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "source_type": r.get("source_type", ""),
                    "chunk_index": r.get("chunk_index", 0),
                    "run_id": r.get("run_id", ""),
                    "score": r.get("_distance", 1.0),
                }
                for r in results
            ]
        except Exception:
            return []

    def delete_by_run(self, run_id: str) -> None:
        """Delete all chunks for a given run_id."""
        if self._table_name not in self._db.table_names():
            return
        table = self._db.open_table(self._table_name)
        try:
            table.delete(f"run_id = '{run_id}'")
        except Exception:
            pass

    def count(self) -> int:
        """Return total number of chunks stored."""
        if self._table_name not in self._db.table_names():
            return 0
        try:
            return self._db.open_table(self._table_name).count_rows()
        except Exception:
            return 0
