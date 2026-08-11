"""
Temporal client helpers — start durable research workflows when a server is available.

Falls back gracefully so ultra-long mode never hard-fails without Temporal.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional


def temporal_configured() -> bool:
    """True if Temporal address is set (server may or may not be up)."""
    return bool(os.getenv("TEMPORAL_SERVER_ADDRESS") or os.getenv("TEMPORAL_HOST"))


def _address() -> str:
    return (
        os.getenv("TEMPORAL_SERVER_ADDRESS")
        or os.getenv("TEMPORAL_HOST")
        or "localhost:7233"
    )


def _task_queue() -> str:
    return os.getenv("TEMPORAL_TASK_QUEUE", "research-agent")


async def _start_research_workflow_async(
    query: str,
    config: Dict[str, Any],
    autonomy: str = "L1",
) -> str:
    from temporalio.client import Client
    from src.engine.temporal.workflows import ResearchWorkflow, HumanInLoopWorkflow

    client = await Client.connect(_address())
    workflow_id = f"research-{config.get('run_id') or os.urandom(4).hex()}"

    wf = HumanInLoopWorkflow if str(autonomy).upper() == "L2" else ResearchWorkflow
    handle = await client.start_workflow(
        wf.run,
        args=[query, config],
        id=workflow_id,
        task_queue=_task_queue(),
    )
    # Wait for result (can be hours for ultra-long)
    result = await handle.result()
    return result if isinstance(result, str) else str(result)


def try_run_temporal_research(
    query: str,
    mode: str = "ultra-long",
    autonomy: str = "L1",
    config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Start a Temporal research workflow and block until complete.

    Returns report markdown on success, or None if Temporal is unavailable
    (caller should fall back to in-process LangGraph).
    """
    cfg = dict(config or {})
    cfg.setdefault("mode", mode)
    cfg.setdefault("autonomy", autonomy)
    cfg.setdefault("query", query)

    try:
        return asyncio.run(_start_research_workflow_async(query, cfg, autonomy=autonomy))
    except Exception as e:
        print(f"  [temporal] unavailable or failed ({e}) — falling back to in-process graph")
        return None
