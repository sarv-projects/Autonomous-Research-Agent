# Temporal durable execution

Ultra-long research (`--mode ultra-long`) can run as a **Temporal workflow** for crash recovery, long timeouts, and human-in-the-loop gates (autonomy L2).

## Architecture

```
CLI / API  →  try_run_temporal_research()  →  Temporal Server  →  Worker
                     │ fail / unavailable
                     └→ in-process LangGraph (fallback)
```

| Piece | Role |
|-------|------|
| `src/engine/temporal/workflows.py` | `ResearchWorkflow`, `HumanInLoopWorkflow` |
| `src/engine/temporal/activities.py` | Plan / research / synthesize / approval activities |
| `src/engine/temporal/client.py` | Client start + wait |
| `main.py worker` | Worker process |

## Local setup

### 1. Temporal server (dev)

```bash
# Option A: Temporal CLI dev server
temporal server start-dev

# Option B: Docker (example)
docker run -d --name temporal -p 7233:7233 temporalio/auto-setup:latest
```

Default address: `localhost:7233`.

### 2. Environment

```bash
# .env
TEMPORAL_SERVER_ADDRESS=localhost:7233
TEMPORAL_TASK_QUEUE=research-agent
```

### 3. Start a worker

```bash
uv run python main.py worker
```

Keep the worker running for the duration of long research jobs.

### 4. Start research

```bash
uv run python main.py research "Post-quantum cryptography landscape" --mode ultra-long --autonomy L1
```

Or L2 (HITL) — approvals appear at `GET /api/approvals` and in the web UI banner:

```bash
uv run python main.py research "Topic" --mode ultra-long --autonomy L2
uv run python main.py server   # another terminal — respond via UI or API
```

## Fallback behavior

If Temporal is not running or the client fails, the agent **automatically falls back** to the in-process LangGraph multi-agent graph so research still completes.

## Production notes

1. Run Temporal cluster with persistence (not only `start-dev`).
2. Run **N workers** behind the same `TEMPORAL_TASK_QUEUE`.
3. Set activity timeouts appropriately for deep modes (see workflow definitions).
4. Prefer L3 autonomy only with hard budget caps and monitoring.
5. Wire alerts on workflow failures via Temporal visibility / Prometheus.

## Related

- [GATEWAY.md](GATEWAY.md) — LLM resilience (used inside activities)
- [ARCHITECTURE.md](ARCHITECTURE.md) — full system topology
- [SPEC.md](SPEC.md) — product requirements
