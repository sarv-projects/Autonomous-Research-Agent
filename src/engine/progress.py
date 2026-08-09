"""
Progress Tracker — shared, thread-safe state for real-time research progress.

Used by:
  - Research graph nodes (update stage, sections, stats)
  - Dashboard SSE endpoint (poll for /api/research/progress)
  - CLI streaming output (read current state)

All updates are atomic via a threading lock.
"""

from __future__ import annotations

import threading
import time


class ResearchProgress:
    """Thread-safe tracker for a research run's progress.

    Graph nodes call update() as they advance through stages.
    The dashboard SSE endpoint calls snapshot() to get the current state.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._reset()

    def _reset(self) -> None:
        with self._lock:
            self.run_id: str = ""
            self.query: str = ""
            self.stage: str = "idle"
            self.iteration: int = 0
            self.max_iterations: int = 6
            self.findings_count: int = 0
            self.factoids_count: int = 0
            self.sections: list[dict] = []
            self.current_section: str = ""
            self.section_index: int = 0
            self.total_sections: int = 0
            self.status: str = ""
            self.elapsed_s: float = 0.0
            self.started_at: float = 0.0
            self.finished: bool = False
            self.error: str = ""

    def start(self, query: str, run_id: str = "", max_iterations: int = 6) -> None:
        with self._lock:
            self._reset()
            self.run_id = run_id
            self.query = query
            self.max_iterations = max_iterations
            self.stage = "starting"
            self.status = "Starting research..."
            self.started_at = time.time()

    def update(
        self,
        stage: str = "",
        iteration: int = -1,
        findings_count: int = -1,
        factoids_count: int = -1,
        sections: list[dict] | None = None,
        current_section: str = "",
        section_index: int = -1,
        total_sections: int = -1,
        status: str = "",
        error: str = "",
        finished: bool | None = None,
    ) -> None:
        """Update progress fields. Only provided fields are changed."""
        with self._lock:
            if stage:
                self.stage = stage
            if iteration >= 0:
                self.iteration = iteration
            if findings_count >= 0:
                self.findings_count = findings_count
            if factoids_count >= 0:
                self.factoids_count = factoids_count
            if sections is not None:
                self.sections = sections
            if current_section:
                self.current_section = current_section
            if section_index >= 0:
                self.section_index = section_index
            if total_sections >= 0:
                self.total_sections = total_sections
            if status:
                self.status = status
            if error:
                self.error = error
            if finished is not None:
                self.finished = finished
            self.elapsed_s = time.time() - self.started_at if self.started_at else 0

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot of current progress."""
        with self._lock:
            return {
                "run_id": self.run_id,
                "query": self.query,
                "stage": self.stage,
                "iteration": self.iteration,
                "max_iterations": self.max_iterations,
                "findings_count": self.findings_count,
                "factoids_count": self.factoids_count,
                "sections": [
                    {"title": s.get("title", ""), "chars": len(s.get("content", ""))}
                    for s in self.sections
                ],
                "current_section": self.current_section,
                "section_progress": f"{self.section_index}/{self.total_sections}"
                if self.total_sections else "",
                "status": self.status,
                "elapsed_s": round(self.elapsed_s, 1),
                "finished": self.finished,
                "error": self.error,
            }


# Module-level singleton — graph nodes write, dashboard reads
CURRENT_PROGRESS = ResearchProgress()


def get_progress() -> ResearchProgress:
    """Get the global progress tracker."""
    return CURRENT_PROGRESS
