"""In-process async research job registry (shared state for long runs)."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Optional


class ResearchJob:
    def __init__(self, query: str, mode: str = "standard", autonomy: str = "L1") -> None:
        self.job_id = f"job_{uuid.uuid4().hex[:12]}"
        self.query = query
        self.mode = mode
        self.autonomy = autonomy
        self.status = "queued"  # queued|running|complete|error|aborted
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.error = ""
        self.run_id = ""
        self.plan: dict = {}
        self.learned: list[str] = []
        self.gaps: list[str] = []
        self.next_action = ""
        self.thoughts: list[dict] = []
        self.report = ""
        self.markdown_path = ""
        self.findings_count = 0
        self.sources_count = 0
        self.iterations = 0
        self.stage = "queued"

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "query": self.query,
            "mode": self.mode,
            "autonomy": self.autonomy,
            "status": self.status,
            "stage": self.stage,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_s": round(
                (self.finished_at or time.time()) - (self.started_at or self.created_at), 1
            ),
            "error": self.error,
            "plan": self.plan,
            "learned": self.learned[-20:],
            "gaps": self.gaps[-20:],
            "next_action": self.next_action,
            "thoughts": self.thoughts[-30:],
            "findings_count": self.findings_count,
            "sources_count": self.sources_count,
            "iterations": self.iterations,
            "report": (self.report or "")[:50000],
            "markdown_path": self.markdown_path,
            "finished": self.status in ("complete", "error", "aborted"),
        }


class JobRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, ResearchJob] = {}

    def create(self, query: str, mode: str = "standard", autonomy: str = "L1") -> ResearchJob:
        job = ResearchJob(query, mode=mode, autonomy=autonomy)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[ResearchJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
            return [j.to_dict() for j in jobs[:limit]]

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in fields.items():
                if hasattr(job, k) and v is not None:
                    setattr(job, k, v)

    def add_thought(self, job_id: str, kind: str, text: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.thoughts.append({"ts": time.time(), "kind": kind, "text": text[:500]})
            if kind == "learned":
                job.learned.append(text[:300])
            elif kind == "gap":
                job.gaps.append(text[:300])
            elif kind == "next":
                job.next_action = text[:300]


JOBS = JobRegistry()


def get_jobs() -> JobRegistry:
    return JOBS
