# Implementation TODO

**End-to-end task list for Autonomous Research Agent**  
**Based on ROADMAP.md phases A-L**  
**Last updated:** 2026-08-08

---

## Overview

This document breaks down all implementation phases into actionable tasks with subtasks. Tasks are organized by phase and include dependencies, estimated complexity, and acceptance criteria.

**Legend:**
- 🔴 High priority / critical path
- 🟡 Medium priority
- 🟢 Low priority / nice-to-have
- ⏳ Blocked by dependency
- ✅ Completed (when applicable)

---

## Phase A — Providers + modes + CLI surfaces

**Goal:** Enable key-optional OpenCode free default, provider presets, and basic CLI commands.

### A.1 Provider Configuration System
- [ ] 🔴 Design provider slot configuration schema
  - [ ] Define `ProviderSlot` data structure (base_url, api_key, models)
  - [ ] Define empty URL = OpenCode free convention
  - [ ] Define empty key = no auth convention
  - [ ] Design `+` provider/model syntax
- [ ] 🔴 Implement provider catalog loader
  - [ ] Create `src/providers/catalog.py`
  - [ ] Load presets from `config/providers.example.yaml`
  - [ ] Implement preset definitions (NIM, OpenRouter, OpenAI, Claude, Gemini, Groq, DeepSeek v4, MiMo, North Mini)
  - [ ] Add provider slot validation
- [ ] 🔴 Implement `+` provider/model registration
  - [ ] Add runtime provider registration API
  - [ ] Implement `GET /models` integration for custom providers
  - [ ] Add model ID validation
- [ ] 🔴 Wire empty URL/key to OpenCode free
  - [ ] Update gateway to handle empty URL → `https://opencode.ai/zen/v1`
  - [ ] Update gateway to omit `Authorization` header when key empty
  - [ ] Register OpenCode free models by default
  - [ ] Test with `deepseek-v4-flash-free`, `big-pickle`, `mimo-v2.5-free`

### A.2 Modes + Budgets System
- [ ] 🟡 Design mode configuration schema
  - [ ] Define `Mode` data structure (name, budgets, quality_dials)
  - [ ] Define budget types (tokens, cost, time, tool_calls)
  - [ ] Define quality dials (ultra-fast, balanced, accurate, comprehensive)
- [ ] 🟡 Implement mode loader
  - [ ] Create `src/engine/modes.py`
  - [ ] Load modes from `config/modes.yaml`
  - [ ] Implement mode validation
- [ ] 🟡 Integrate modes with gateway
  - [ ] Pass mode context to gateway calls
  - [ ] Enforce budget limits per mode
  - [ ] Track spend per mode in metrics

### A.3 CLI Commands
- [ ] 🔴 Implement `doctor` command
  - [ ] Create `main.py doctor` entry point
  - [ ] List configured providers
  - [ ] Test provider connectivity
  - [ ] Display available models
  - [ ] Show gateway status
- [ ] 🟡 Implement `chat` command stub
  - [ ] Create `main.py chat` entry point
  - [ ] Basic chat loop with gateway LLM
  - [ ] Add `--mode` flag
  - [ ] Add `--provider` flag
- [ ] 🟡 Enhance `research` command
  - [ ] Add `--mode` flag
  - [ ] Add `--provider` flag
  - [ ] Add `--autonomy` flag (L1/L2/L3)
  - [ ] Improve output formatting

### A.4 Configuration Files
- [ ] 🔴 Create `config/providers.example.yaml`
  - [ ] Define OpenCode free preset
  - [ ] Define NIM preset
  - [ ] Define OpenRouter preset
  - [ ] Define OpenAI preset
  - [ ] Define Claude preset
  - [ ] Define Gemini preset
  - [ ] Define Groq preset
  - [ ] Define DeepSeek v4 preset
- [ ] 🟡 Create `config/modes.yaml`
  - [ ] Define ultra-fast mode
  - [ ] Define balanced mode
  - [ ] Define accurate mode
  - [ ] Define comprehensive mode
- [ ] 🔴 Update `.env.example`
  - [ ] Add optional provider keys
  - [ ] Add mode configuration examples
  - [ ] Add documentation for provider setup

### A.5 Testing
- [ ] 🔴 Write provider configuration tests
  - [ ] Test empty URL → OpenCode free
  - [ ] Test empty key → no auth
  - [ ] Test `+` provider registration
  - [ ] Test preset loading
- [ ] 🟡 Write mode system tests
  - [ ] Test mode loading
  - [ ] Test budget enforcement
  - [ ] Test quality dial selection
- [ ] 🔴 Write CLI command tests
  - [ ] Test `doctor` command
  - [ ] Test `chat` command stub
  - [ ] Test `research` command flags

**Acceptance Criteria:**
- ✅ Chat works on Zen free without API key
- ✅ `doctor` command lists providers and tests connectivity
- ✅ Modes are configurable and enforce budgets
- ✅ Provider presets work out of the box

---

## Phase B — RAG + VectorStore

**Goal:** Implement chunking, embedding, vector storage, and retrieval for token-efficient RAG.

### B.1 Chunking System
- [ ] 🔴 Design chunking strategy
  - [ ] Define chunk size (500-800 tokens)
  - [ ] Define overlap (10%)
  - [ ] Define metadata schema (run_id, url, title, source_type, chunk_id)
- [ ] 🔴 Implement chunker
  - [ ] Create `src/rag/chunk.py`
  - [ ] Implement token-based chunking
  - [ ] Implement overlap handling
  - [ ] Implement metadata extraction
- [ ] 🟡 Add specialized chunking
  - [ ] PDF-aware chunking (respect sections)
  - [ ] Code-aware chunking (respect functions)
  - [ ] Table-aware chunking

### B.2 Embedding System
- [ ] 🔴 Design embedding interface
  - [ ] Define `Embedder` protocol
  - [ ] Define embedding model selection
- [ ] 🔴 Implement embedder
  - [ ] Create `src/rag/embed.py`
  - [ ] Implement OpenAI embeddings
  - [ ] Implement fallback to local models
  - [ ] Add caching layer
- [ ] 🟡 Add batch embedding
  - [ ] Implement parallel batch processing
  - [ ] Add rate limiting
  - [ ] Add error handling

### B.3 Vector Storage
- [ ] 🔴 Design vector store interface
  - [ ] Define `VectorStore` protocol
  - [ ] Define `upsert`, `query`, `hybrid_query`, `delete` methods
- [ ] 🔴 Implement LanceDB backend
  - [ ] Create `src/rag/backends/lancedb.py`
  - [ ] Implement `upsert`
  - [ ] Implement `query` (vector similarity)
  - [ ] Implement `hybrid_query` (vector + FTS)
  - [ ] Implement `delete`
- [ ] 🟡 Implement Qdrant backend
  - [ ] Create `src/rag/backends/qdrant.py`
  - [ ] Implement all VectorStore methods
  - [ ] Add Qdrant client configuration
- [ ] 🟡 Implement SQLite FTS5 fallback
  - [ ] Create `src/rag/backends/fts.py`
  - [ ] Implement FTS indexing
  - [ ] Implement keyword search
- [ ] 🔴 Add backend selection
  - [ ] Implement `VECTOR_BACKEND` env var
  - [ ] Default to LanceDB
  - [ ] Add backend factory

### B.4 RAG Pipeline
- [ ] 🔴 Implement ingestion pipeline
  - [ ] Create `src/rag/pipeline.py`
  - [ ] Implement `gather → chunk → embed → upsert` flow
  - [ ] Add progress tracking
  - [ ] Add error handling
- [ ] 🔴 Implement retrieval pipeline
  - [ ] Implement `query → embed → hybrid_query` flow
  - [ ] Implement top-k selection
  - [ ] Implement metadata filtering
  - [ ] Add relevance scoring
- [ ] 🟡 Add retrieval optimization
  - [ ] Implement query expansion
  - [ ] Implement re-ranking
  - [ ] Implement diversity selection

### B.5 Integration with Research Pipeline
- [ ] 🔴 Integrate ingestion into research
  - [ ] Add `ingest` node to research graph
  - [ ] Connect after `gather` node
  - [ ] Pass chunks to vector store
- [ ] 🔴 Integrate retrieval into research
  - [ ] Add `retrieve` node to research graph
  - [ ] Connect before `analyze` node
  - [ ] Pass retrieved chunks to analyzer
- [ ] 🔴 Verify token reduction
  - [ ] Measure tokens before/after RAG
  - [ ] Ensure full page bodies never enter LLM context
  - [ ] Validate retrieval quality

### B.6 Testing
- [ ] 🔴 Write chunking tests
  - [ ] Test chunk size accuracy
  - [ ] Test overlap handling
  - [ ] Test metadata extraction
- [ ] 🔴 Write embedding tests
  - [ ] Test embedding generation
  - [ ] Test caching
  - [ ] Test fallback behavior
- [ ] 🔴 Write vector store tests
  - [ ] Test LanceDB backend
  - [ ] Test Qdrant backend
  - [ ] Test FTS fallback
  - [ ] Test backend selection
- [ ] 🔴 Write RAG pipeline tests
  - [ ] Test ingestion pipeline
  - [ ] Test retrieval pipeline
  - [ ] Test integration with research

**Acceptance Criteria:**
- ✅ Synthesis/section paths never receive full multi-page dumps
- ✅ Token reduction measured and significant (>50%)
- ✅ Retrieval quality maintains or improves research output
- ✅ LanceDB works by default; Qdrant and FTS fallbacks functional

---

## Phase C — Multi-iteration research + multi-agent skeleton

**Goal:** Implement multi-agent research with progressive output and citation ship-gate.

### C.1 Multi-Agent Framework
- [ ] 🔴 Design agent interface
  - [ ] Define `Agent` protocol
  - [ ] Define agent lifecycle (init, execute, cleanup)
  - [ ] Define agent communication patterns
- [ ] 🔴 Implement agent registry
  - [ ] Create `src/engine/agents/registry.py`
  - [ ] Implement agent registration
  - [ ] Implement agent discovery
  - [ ] Add agent validation

### C.2 Core Agents
- [ ] 🔴 Implement Planner agent
  - [ ] Create `src/engine/agents/planner.py`
  - [ ] Implement query decomposition
  - [ ] Implement DAG generation
  - [ ] Implement budget allocation
  - [ ] Implement tool plan generation
- [ ] 🔴 Implement Researcher agent
  - [ ] Create `src/engine/agents/researcher.py`
  - [ ] Implement tool execution
  - [ ] Implement RAG integration
  - [ ] Implement claim extraction
- [ ] 🔴 Implement Critic agent
  - [ ] Create `src/engine/agents/critic.py`
  - [ ] Implement quality scoring
  - [ ] Implement citation sampling
  - [ ] Implement gap identification
  - [ ] Implement retry/replan triggering
- [ ] 🔴 Implement Synthesizer agent
  - [ ] Create `src/engine/agents/synthesizer.py`
  - [ ] Implement progressive section writing
  - [ ] Implement RAG-based drafting
  - [ ] Implement streaming output
- [ ] 🔴 Implement Compiler agent
  - [ ] Create `src/engine/agents/compiler.py`
  - [ ] Implement report assembly
  - [ ] Implement citation ship-gate
  - [ ] Implement export functionality

### C.3 Research Graph
- [ ] 🔴 Redesign research graph for multi-agent
  - [ ] Create `src/engine/graph_research.py`
  - [ ] Implement agent orchestration
  - [ ] Implement state management
  - [ ] Implement agent handoffs
- [ ] 🔴 Implement multi-iteration loop
  - [ ] Add `reflect` node
  - [ ] Implement continue/stop logic
  - [ ] Implement gap-driven iteration
  - [ ] Add iteration limit (configurable)
- [ ] 🔴 Implement progressive output
  - [ ] Stream outline first
  - [ ] Stream sections progressively
  - [ ] Update CLI/UI per section
  - [ ] Add progress indicators

### C.4 Citation System
- [ ] 🔴 Design citation schema
  - [ ] Define `Citation` data structure
  - [ ] Define claim→source mapping
  - [ ] Define inline citation format
- [ ] 🔴 Implement citation tracking
  - [ ] Track claims with evidence IDs
  - [ ] Track source references
  - [ ] Implement citation indexing
- [ ] 🔴 Implement citation ship-gate
  - [ ] Validate citations before export
  - [ ] Block export if key claims uncited
  - [ ] Generate end Sources section
  - [ ] Implement citation sampling for verification

### C.5 Autonomy Levels
- [ ] 🟡 Implement L1 (Report)
  - [ ] Default behavior
  - [ ] Human always reviews
  - [ ] No automatic actions
- [ ] 🟡 Implement L2 (Human gate)
  - [ ] Pause after plan
  - [ ] Pause before expensive waves
  - [ ] Pause before export
  - [ ] Add approval prompts
- [ ] 🟡 Implement L3 (Unattended)
  - [ ] Auto-run within budgets
  - [ ] Hard budget enforcement
  - [ ] Full audit logging
  - [ ] Emergency stop mechanism

### C.6 Testing
- [ ] 🔴 Write agent tests
  - [ ] Test Planner agent
  - [ ] Test Researcher agent
  - [ ] Test Critic agent
  - [ ] Test Synthesizer agent
  - [ ] Test Compiler agent
- [ ] 🔴 Write graph tests
  - [ ] Test multi-agent orchestration
  - [ ] Test iteration loop
  - [ ] Test progressive output
- [ ] 🔴 Write citation tests
  - [ ] Test citation tracking
  - [ ] Test ship-gate logic
  - [ ] Test citation validation

**Acceptance Criteria:**
- ✅ Multi-iter cited report with clear agent boundaries in traces
- ✅ Progressive output streams section-by-section
- ✅ Citation ship-gate blocks uncited reports
- ✅ Autonomy levels L1-L3 configurable and functional

---

## Phase C2 — Thinker agent (Gemini free)

**Goal:** Implement large-context reasoning agent for plan refinement and contradiction resolution.

### C2.1 Gemini Provider Integration
- [ ] 🔴 Add Gemini provider to catalog
  - [ ] Add Gemini base URL to `PROVIDERS.md`
  - [ ] Add Gemini model IDs (Flash, Pro)
  - [ ] Add Gemini auth documentation
- [ ] 🔴 Implement Gemini adapter
  - [ ] Create `src/providers/gemini.py`
  - [ ] Implement OpenAI-compat endpoint
  - [ ] Handle Gemini-specific features
  - [ ] Add rate limit handling

### C2.2 Thinker Agent Implementation
- [ ] 🔴 Implement Thinker agent
  - [ ] Create `src/engine/agents/thinker.py`
  - [ ] Implement large-context reasoning
  - [ ] Disable tool calls (read-only)
  - [ ] Implement structured JSON output
- [ ] 🔴 Define Thinker invocation logic
  - [ ] Invoke on large context steps
  - [ ] Invoke on plan refinement
  - [ ] Invoke on contradiction sets
  - [ ] Skip on micro-steps
- [ ] 🔴 Implement rate limit policy
  - [ ] Respect Gemini free RPM/TPM/RPD
  - [ ] Implement queue for Thinker jobs
  - [ ] Implement backoff on 429
  - [ ] Add rate limit metrics

### C2.3 Fallback Chain
- [ ] 🟡 Implement fallback logic
  - [ ] Fallback to OpenCode free strong
  - [ ] Fallback to Groq
  - [ ] Fallback to DeepSeek v4
  - [ ] Log fallback events

### C2.4 Testing
- [ ] 🔴 Write Thinker agent tests
  - [ ] Test large-context reasoning
  - [ ] Test structured output
  - [ ] Test rate limiting
  - [ ] Test fallback chain

**Acceptance Criteria:**
- ✅ Deep runs use Thinker for plan/contradiction steps
- ✅ Thinker respects Gemini free rate limits
- ✅ Fallback chain works when Gemini quota exhausted
- ✅ Thinker never calls tools (smaller trust boundary)

---

## Phase C3 — Temporal integration (durable execution)

**Goal:** Enable 24h+ research runs with crash recovery and human-in-the-loop workflows.

### C3.1 Temporal Infrastructure
- [ ] 🔴 Install Temporal dependencies
  - [ ] Add `temporalio` to dependencies
  - [ ] Update `INSTALL.md` with Temporal setup
  - [ ] Add Temporal to `.env.example`
- [ ] 🔴 Configure Temporal server
  - [ ] Create `config/temporal.yaml`
  - [ ] Define server address
  - [ ] Define namespace
  - [ ] Define task queue
  - [ ] Define workflow timeout
  - [ ] Define activity timeout
  - [ ] Define retry policy

### C3.2 Temporal Workflow Integration
- [ ] 🔴 Create Temporal workflow module
  - [ ] Create `src/engine/temporal/`
  - [ ] Implement workflow definitions
  - [ ] Implement activity workers
  - [ ] Implement client connection
- [ ] 🔴 Wrap research graph as workflow
  - [ ] Convert `graph_research.py` to Temporal workflow
  - [ ] Define workflow inputs/outputs
  - [ ] Implement workflow state management
- [ ] 🔴 Convert nodes to activities
  - [ ] Convert Planner to activity
  - [ ] Convert Researcher to activity
  - [ ] Convert Thinker to activity
  - [ ] Convert Critic to activity
  - [ ] Convert Synthesizer to activity
  - [ ] Convert Compiler to activity

### C3.3 Gateway + Temporal Integration
- [ ] 🔴 Implement Temporal activity wrapper
  - [ ] Create `src/gateway/temporal.py`
  - [ ] Wrap `call_llm` as Temporal activity
  - [ ] Configure activity options
  - [ ] Add retry policies
- [ ] 🔴 Persist gateway state
  - [ ] Persist circuit breaker state
  - [ ] Persist metrics
  - [ ] Persist budget state

### C3.4 Human-in-the-Loop
- [ ] 🟡 Implement pause/approval activities
  - [ ] Add pause after plan
  - [ ] Add pause before expensive operations
  - [ ] Add approval prompts
  - [ ] Implement resume logic
- [ ] 🟡 Implement workflow interruption
  - [ ] Add stop signal handling
  - [ ] Implement graceful shutdown
  - [ ] Add workflow cancellation

### C3.5 Crash Recovery
- [ ] 🔴 Implement workflow resumption
  - [ ] Auto-resume on restart
  - [ ] Restore workflow state
  - [ ] Continue from last checkpoint
- [ ] 🔴 Implement checkpointing
  - [ ] Define checkpoint intervals
  - [ ] Persist workflow state
  - [ ] Implement checkpoint restoration

### C3.6 Testing
- [ ] 🔴 Write Temporal workflow tests
  - [ ] Test workflow execution
  - [ ] Test activity execution
  - [ ] Test crash recovery
  - [ ] Test checkpointing
- [ ] 🔴 Write HITL tests
  - [ ] Test pause/approval
  - [ ] Test workflow interruption
  - [ ] Test resume logic

**Acceptance Criteria:**
- ✅ Research runs survive crashes and restarts
- ✅ 24h+ execution supported with checkpoints
- ✅ Human-in-the-loop pause/approval functional
- ✅ Gateway state persists across checkpoints

---

## Phase D — MCP tool bus + document parsers

**Goal:** Implement modular tool system with MCP and document parsing capabilities.

### D.1 MCP Infrastructure
- [ ] 🔴 Design MCP manager
  - [ ] Define MCP server interface
  - [ ] Define tool registration schema
  - [ ] Define tool execution protocol
- [ ] 🔴 Implement MCP manager
  - [ ] Create `src/tools/mcp_manager.py`
  - [ ] Implement MCP server discovery
  - [ ] Implement tool registration
  - [ ] Implement tool execution
  - [ ] Implement error handling

### D.2 Tool Registry
- [ ] 🔴 Implement tool registry
  - [ ] Create `src/tools/registry.py`
  - [ ] Implement tool registration
  - [ ] Implement tool discovery
  - [ ] Implement capability tags
  - [ ] Implement tool selection

### D.3 Tool Executor
- [ ] 🔴 Implement tool executor
  - [ ] Create `src/tools/executor.py`
  - [ ] Implement parallel execution
  - [ ] Implement timeout handling
  - [ ] Implement result aggregation
  - [ ] Implement error recovery

### D.4 MCP Tool Adapters
- [ ] 🟡 Implement Wikipedia adapter
  - [ ] Create `src/tools/adapters/wikipedia.py`
  - [ ] Implement search
  - [ ] Implement page fetch
  - [ ] Add to registry
- [ ] 🟡 Implement Firecrawl adapter
  - [ ] Create `src/tools/adapters/firecrawl.py`
  - [ ] Implement web crawling
  - [ ] Implement content extraction
  - [ ] Add to registry
- [ ] 🟡 Implement Exa adapter
  - [ ] Create `src/tools/adapters/exa.py`
  - [ ] Implement search
  - [ ] Implement result filtering
  - [ ] Add to registry

### D.5 Document Parsers
- [ ] 🔴 Implement MinerU adapter
  - [ ] Create `src/tools/adapters/mineru.py`
  - [ ] Implement PDF parsing
  - [ ] Implement DOCX parsing
  - [ ] Implement PPTX parsing
  - [ ] Implement XLSX parsing
  - [ ] Implement formula→LaTeX conversion
  - [ ] Implement table→HTML conversion
  - [ ] Add to registry
- [ ] 🟡 Implement Nougat adapter
  - [ ] Create `src/tools/adapters/nougat.py`
  - [ ] Implement academic PDF parsing
  - [ ] Handle LaTeX math heavy documents
  - [ ] Add license checks (CC-BY-NC)
  - [ ] Add to registry

### D.6 Tool Selection
- [ ] 🟡 Implement tool selection component
  - [ ] Implement capability matching
  - [ ] Implement tool ranking
  - [ ] Implement tool fallback
  - [ ] Add tool selection evaluation

### D.7 Integration
- [ ] 🔴 Integrate tools with research
  - [ ] Connect tool executor to Researcher agent
  - [ ] Add tool selection to Planner
  - [ ] Implement tool result processing
  - [ ] Add tool usage tracking

### D.8 Testing
- [ ] 🔴 Write MCP manager tests
  - [ ] Test server discovery
  - [ ] Test tool registration
  - [ ] Test tool execution
- [ ] 🔴 Write adapter tests
  - [ ] Test Wikipedia adapter
  - [ ] Test Firecrawl adapter
  - [ ] Test Exa adapter
  - [ ] Test MinerU adapter
  - [ ] Test Nougat adapter
- [ ] 🔴 Write tool selection tests
  - [ ] Test capability matching
  - [ ] Test tool ranking
  - [ ] Test fallback logic

**Acceptance Criteria:**
- ✅ Tools pluggable without graph rewrite
- ✅ PDF URLs can be ingested cleanly via MinerU
- ✅ MCP tools work via registry
- ✅ Tool selection component functional

---

## Phase E — Bias mitigation (Triangulator agent)

**Goal:** Implement adversarial triangulation for subjective/controversial queries.

### E.1 Triangulator Agent
- [ ] 🔴 Implement Triangulator agent
  - [ ] Create `src/engine/agents/triangulator.py`
  - [ ] Implement Pro agent
  - [ ] Implement Con agent
  - [ ] Implement Neutral agent
  - [ ] Implement Synthesis Arbiter
- [ ] 🔴 Define system prompts
  - [ ] Pro agent system prompt (argue for)
  - [ ] Con agent system prompt (argue against)
  - [ ] Neutral agent system prompt (balanced view)
  - [ ] Arbiter system prompt (bias detection)
- [ ] 🔴 Implement multi-provider setup
  - [ ] Configure OpenAI for one agent
  - [ ] Configure Anthropic for one agent
  - [ ] Configure Google for one agent
  - [ ] Add provider rotation

### E.2 Bias Detection
- [ ] 🔴 Implement bias detection logic
  - [ ] Cross-agent critique
  - [ ] Identify biased framing
  - [ ] Score bias level
  - [ ] Generate bias assessment
- [ ] 🔴 Implement synthesis
  - [ ] Compare agent outputs
  - [ ] Find common ground
  - [ ] Generate neutral synthesis
  - [ ] Include bias score

### E.3 Integration
- [ ] 🔴 Integrate with research pipeline
  - [ ] Detect subjective/controversial queries
  - [ ] Trigger Triangulator for subjective queries
  - [ ] Pass synthesis to research
  - [ ] Add bias metadata to output
- [ ] 🔴 Add citation enforcement
  - [ ] Require citations for all claims
  - [ ] Validate citations in synthesis
  - [ ] Block uncited biased claims

### E.4 Testing
- [ ] 🔴 Write Triangulator tests
  - [ ] Test Pro/Con/Neutral agents
  - [ ] Test bias detection
  - [ ] Test synthesis generation
  - [ ] Test citation enforcement
- [ ] 🔴 Write integration tests
  - [ ] Test subjective query detection
  - [ ] Test pipeline integration
  - [ ] Test bias scoring

**Acceptance Criteria:**
- ✅ Subjective questions receive balanced outputs
- ✅ Bias assessment scores included
- ✅ Citations enforced for all claims
- ✅ Multi-provider setup functional

---

## Phase F — Factoid extraction pipeline (token optimization)

**Goal:** Implement structured factoid extraction for 90% token reduction.

### F.1 Local Inference Setup
- [ ] 🔴 Add Ollama support
  - [ ] Add Ollama client to dependencies
  - [ ] Implement Ollama adapter
  - [ ] Add model download (Llama 3 8B, Phi-3)
  - [ ] Update INSTALL.md
- [ ] 🟡 Add vLLM support
  - [ ] Add vLLM to dependencies
  - [ ] Implement vLLM adapter
  - [ ] Add GPU configuration
  - [ ] Update INSTALL.md

### F.2 Factoid Schema
- [ ] 🔴 Define factoid schema
  - [ ] Create `src/rag/factoid/schema.py`
  - [ ] Define `Factoid` data model
  - [ ] Define factoid types (entity, relation, event, statistic, definition, citation, claim, methodology)
  - [ ] Define metadata schema
  - [ ] Add validation

### F.3 Factoid Extractor Agent
- [ ] 🔴 Implement Factoid Extractor
  - [ ] Create `src/rag/factoid/extractor.py`
  - [ ] Implement system prompt
  - [ ] Implement chunk→factoid conversion
  - [ ] Implement confidence scoring
  - [ ] Implement metadata extraction
- [ ] 🔴 Implement batch processing
  - [ ] Implement parallel chunk processing
  - [ ] Add rate limiting
  - [ ] Add error handling
  - [ ] Add progress tracking

### F.4 Factoid Storage
- [ ] 🔴 Implement factoid store
  - [ ] Create `src/rag/factoid/store.py`
  - [ ] Implement factoid upsert
  - [ ] Implement factoid embedding
  - [ ] Implement metadata indexing
  - [ ] Add to vector database

### F.5 Factoid Retrieval
- [ ] 🔴 Implement factoid retriever
  - [ ] Create `src/rag/factoid/retrieve.py`
  - [ ] Implement factoid query
  - [ ] Implement hybrid search
  - [ ] Implement metadata filtering
  - [ ] Convert to Factoid objects

### F.6 Gap-Aware Evidence Assembly
- [ ] 🔴 Implement gap detection
  - [ ] Create `src/rag/factoid/gap_aware.py`
  - [ ] Identify missing factoid types
  - [ ] Generate targeted queries
  - [ ] Retrieve additional factoids
- [ ] 🔴 Implement evidence assembly
  - [ ] Assemble factoids by type
  - [ ] Reconstruct context
  - [ ] Optimize for synthesis

### F.7 Context Reconstruction
- [ ] 🔴 Implement context reconstruction
  - [ ] Group factoids by type
  - [ ] Build structured context
  - [ ] Integrate with Synthesizer
  - [ ] Validate reconstruction quality

### F.8 Integration
- [ ] 🔴 Integrate with ingestion
  - [ ] Add `extract_factoids` node
  - [ ] Connect after chunking
  - [ ] Store factoids in vector DB
- [ ] 🔴 Integrate with retrieval
  - [ ] Modify `retrieve` node to use factoids
  - [ ] Update Synthesizer to use factoid context
  - [ ] Validate token reduction

### F.9 Testing
- [ ] 🔴 Write factoid extraction tests
  - [ ] Test extractor agent
  - [ ] Test schema validation
  - [ ] Test confidence scoring
- [ ] 🔴 Write storage tests
  - [ ] Test factoid upsert
  - [ ] Test factoid retrieval
  - [ ] Test metadata filtering
- [ ] 🔴 Write gap-aware tests
  - [ ] Test gap detection
  - [ ] Test evidence assembly
- [ ] 🔴 Write integration tests
  - [ ] Test ingestion integration
  - [ ] Test retrieval integration
  - [ ] Measure token reduction

**Acceptance Criteria:**
- ✅ RAG operates on compressed factoids
- ✅ 90% token reduction achieved
- ✅ Quality maintained or improved
- ✅ Gap-aware evidence assembly functional

---

## Phase G — Retriever Guard (source verification)

**Goal:** Implement source credibility filtering to reduce hallucination risk.

### G.1 Retriever Guard Agent
- [ ] 🔴 Implement Retriever Guard
  - [ ] Create `src/engine/agents/retriever_guard.py`
  - [ ] Implement source analysis
  - [ ] Implement credibility scoring
  - [ ] Implement source filtering

### G.2 Domain Reputation
- [ ] 🔴 Implement domain analysis
  - [ ] Add external API integration (or heuristics)
  - [ ] Implement domain age check
  - [ ] Implement domain authority check
  - [ ] Cache domain reputation

### G.3 Content Analysis
- [ ] 🔴 Implement content freshness
  - [ ] Extract publication dates
  - [ ] Compare to query recency requirements
  - [ ] Filter outdated content
- [ ] 🔴 Implement citation quality
  - [ ] Analyze citation density
  - [ ] Assess citation sources
  - [ ] Score citation quality

### G.4 Source Filtering
- [ ] 🔴 Implement blocking logic
  - [ ] Block hallucinated URLs
  - [ ] Block SEO spam
  - [ ] Block content farms
  - [ ] Maintain blocklist
- [ ] 🔴 Implement promotion logic
  - [ ] Promote peer-reviewed sources
  - [ ] Promote official documentation
  - [ ] Promote reputable news
  - [ ] Maintain allowlist

### G.5 Bias Detection
- [ ] 🟡 Integrate with Triangulator
  - [ ] Trigger bias detection for controversial sources
  - [ ] Use Triangulator for source verification
  - [ ] Add bias metadata to sources

### G.6 Caching
- [ ] 🔴 Implement source caching
  - [ ] Cache trusted sources
  - [ ] Cache blocked sources
  - [ ] Implement cache invalidation
  - [ ] Add cache metrics

### G.7 Integration
- [ ] 🔴 Integrate with search pipeline
  - [ ] Add `verify_sources` node
  - [ ] Connect after `gather`
  - [ ] Pass filtered sources to RAG
  - [ ] Log filtering decisions

### G.8 Testing
- [ ] 🔴 Write Retriever Guard tests
  - [ ] Test domain analysis
  - [ ] Test content freshness
  - [ ] Test citation quality
- [ ] 🔴 Write filtering tests
  - [ ] Test blocking logic
  - [ ] Test promotion logic
  - [ ] Test blocklist/allowlist
- [ ] 🔴 Write integration tests
  - [ ] Test pipeline integration
  - [ ] Test caching
  - [ ] Measure hallucination reduction

**Acceptance Criteria:**
- ✅ Search results filtered for credibility
- ✅ Low-quality sources blocked
- ✅ High-quality sources promoted
- ✅ Hallucination risk reduced

---

## Phase H — Vault + self-improve

**Goal:** Implement cross-run vault, traces, strategy memory, and source quality tracking.

### H.1 Vault System
- [ ] 🔴 Design vault schema
  - [ ] Define vault data model
  - [ ] Define note structure
  - [ ] Define index structure
  - [ ] Define metadata schema
- [ ] 🔴 Implement vault storage
  - [ ] Create `src/vault/storage.py`
  - [ ] Implement vault persistence
  - [ ] Implement vault indexing
  - [ ] Implement vault search
- [ ] 🔴 Implement vault integration
  - [ ] Add sources to vault on run completion
  - [ ] Index vault for search
  - [ ] Implement vault-first on plan

### H.2 Traces System
- [ ] 🔴 Design trace schema
  - [ ] Define trace data model
  - [ ] Define event structure
  - [ ] Define metadata schema
- [ ] 🔴 Implement trace collection
  - [ ] Create `src/improve/traces.py`
  - [ ] Collect agent decisions
  - [ ] Collect tool usage
  - [ ] Collect performance metrics
  - [ ] Store traces as JSONL
- [ ] 🔴 Implement trace analysis
  - [ ] Analyze success patterns
  - [ ] Analyze failure patterns
  - [ ] Extract insights
  - [ ] Update strategy memory

### H.3 Strategy Memory
- [ ] 🔴 Design strategy schema
  - [ ] Define strategy data model
  - [ ] Define tactic structure
  - [ ] Define topic tags
- [ ] 🔴 Implement strategy storage
  - [ ] Create `src/improve/strategy.py`
  - [ ] Store successful tactics
  - [ ] Store topic tags
  - [ ] Implement strategy retrieval
- [ ] 🔴 Implement strategy injection
  - [ ] Match strategies to new queries
  - [ ] Inject into Planner
  - [ ] Track strategy effectiveness

### H.4 Source Quality
- [ ] 🔴 Implement source quality tracking
  - [ ] Track source usage
  - [ ] Track source reliability
  - [ ] Score source quality
  - [ ] Update quality scores over time
- [ ] 🔴 Implement source ranking
  - [ ] Rank sources by quality
  - [ ] Prioritize high-quality sources
  - [ ] Deprioritize low-quality sources

### H.5 Self-Improve Loop
- [ ] 🔴 Implement self-improve pipeline
  - [ ] Run trace analysis on completion
  - [ ] Update strategy memory
  - [ ] Update source quality scores
  - [ ] Update vault
- [ ] 🔴 Implement learning feedback
  - [ ] Use traces for new fixtures
  - [ ] Use strategy memory for planning
  - [ ] Use source quality for retrieval

### H.6 Integration
- [ ] 🔴 Integrate with research pipeline
  - [ ] Add trace collection to all agents
  - [ ] Add vault update on completion
  - [ ] Add strategy injection to Planner
  - [ ] Add source quality to retrieval

### H.7 Testing
- [ ] 🔴 Write vault tests
  - [ ] Test vault storage
  - [ ] Test vault indexing
  - [ ] Test vault search
- [ ] 🔴 Write trace tests
  - [ ] Test trace collection
  - [ ] Test trace analysis
- [ ] 🔴 Write strategy tests
  - [ ] Test strategy storage
  - [ ] Test strategy retrieval
  - [ ] Test strategy injection
- [ ] 🔴 Write integration tests
  - [ ] Test self-improve loop
  - [ ] Test learning feedback

**Acceptance Criteria:**
- ✅ Second similar topic reuses vault before paid fetch
- ✅ Traces collected and analyzed
- ✅ Strategy memory updated and used
- ✅ Source quality tracked and prioritized

---

## Phase I — Critique / fact-check / deep / browser

**Goal:** Implement quality gates, fact-checking, deep mode budgets, and browser escalation.

### I.1 Critic Enhancement
- [ ] 🔴 Implement quality bar
  - [ ] Define quality thresholds
  - [ ] Implement quality scoring
  - [ ] Add quality metrics
- [ ] 🔴 Implement fact-check sample
  - [ ] Sample key claims
  - [ ] Verify against sources
  - [ ] Cross-reference multiple sources
  - [ ] Flag discrepancies
- [ ] 🔴 Implement patch-only polish
  - [ ] Identify specific issues
  - [ ] Generate targeted patches
  - [ ] Apply patches without full regen
  - [ ] Validate patch quality

### I.2 Deep Mode
- [ ] 🔴 Define deep mode budgets
  - [ ] Define deep mode token budget
  - [ ] Define deep mode cost budget
  - [ ] Define deep mode time budget
  - [ ] Define deep mode tool budget
- [ ] 🔴 Implement deep mode logic
  - [ ] Enable additional iterations
  - [ ] Enable deeper retrieval
  - [ ] Enable more comprehensive analysis
  - [ ] Enforce deep mode budgets

### I.3 Browser Escalation
- [ ] 🟡 Implement browser MCP
  - [ ] Add browser tool adapter
  - [ ] Implement browser control
  - [ ] Implement page interaction
  - [ ] Add to registry
- [ ] 🟡 Implement escalation logic
  - [ ] Detect crawl failures
  - [ ] Trigger browser escalation
  - [ ] Fallback to browser when needed
  - [ ] Add timeout handling

### I.4 Autonomy L2 Enhancement
- [ ] 🟡 Enhance L2 human gates
  - [ ] Add quality check gates
  - [ ] Add fact-check gates
  - [ ] Add deep spend gates
  - [ ] Improve approval prompts

### I.5 Testing
- [ ] 🔴 Write Critic tests
  - [ ] Test quality bar
  - [ ] Test fact-check sample
  - [ ] Test patch-only polish
- [ ] 🔴 Write deep mode tests
  - [ ] Test budget enforcement
  - [ ] Test deep mode behavior
- [ ] 🟡 Write browser tests
  - [ ] Test browser MCP
  - [ ] Test escalation logic

**Acceptance Criteria:**
- ✅ Critic quality bar functional
- ✅ Fact-check samples verified
- ✅ Patch-only polish works
- ✅ Deep mode budgets enforced
- ✅ Browser escalation functional

---

## Phase J — Evals harden (EvalOps)

**Goal:** Implement component suite CI, trajectory/efficiency/research rubrics, eval UI, and prompt versioning.

### J.1 Component Evals
- [ ] 🔴 Implement tool selection eval
  - [ ] Create `evals/datasets/tool_selection.jsonl`
  - [ ] Create `evals/scorers/tool_accuracy.py`
  - [ ] Implement runner
- [ ] 🔴 Implement plan coherence eval
  - [ ] Create `evals/datasets/intent_modes.jsonl`
  - [ ] Create `evals/scorers/plan_coherence.py`
  - [ ] Implement LLM judge
- [ ] 🔴 Implement memory recall eval
  - [ ] Create `evals/datasets/memory_multiturn.jsonl`
  - [ ] Create `evals/scorers/memory_recall.py`
- [ ] 🔴 Implement RAG IR eval
  - [ ] Create `evals/datasets/rag_qrels.jsonl`
  - [ ] Create `evals/scorers/rag_ir.py`
  - [ ] Implement recall@k, MRR, nDCG
- [ ] 🔴 Implement citation grounding eval
  - [ ] Create `evals/scorers/citations.py`
  - [ ] Implement entailment check
  - [ ] Implement judge

### J.2 System Evals
- [ ] 🔴 Implement task completion eval
  - [ ] Create `evals/datasets/research_tasks.jsonl`
  - [ ] Create `evals/scorers/task_completion.py`
- [ ] 🔴 Implement trajectory eval
  - [ ] Create `evals/scorers/trajectory.py`
  - [ ] Track cascading failures
  - [ ] Identify first-fail step
- [ ] 🔴 Implement efficiency eval
  - [ ] Create `evals/scorers/efficiency.py`
  - [ ] Track loops, tokens, latency, cost
  - [ ] Compare vs budget
- [ ] 🔴 Implement research quality eval
  - [ ] Create `evals/scorers/research_rubric.py`
  - [ ] Implement coverage rubric
  - [ ] Implement citation rubric
  - [ ] Implement actionability rubric

### J.3 Eval Infrastructure
- [ ] 🔴 Implement component runner
  - [ ] Create `evals/runners/component_runner.py`
  - [ ] Implement parallel execution
  - [ ] Implement result aggregation
- [ ] 🔴 Implement e2e runner
  - [ ] Create `evals/runners/e2e_runner.py`
  - [ ] Implement full research eval
  - [ ] Implement end-to-end metrics
- [ ] 🔴 Implement macro aggregator
  - [ ] Create `evals/runners/macro_aggregator.py`
  - [ ] Aggregate across runs
  - [ ] Identify blockers

### J.4 CI Integration
- [ ] 🔴 Add component evals to CI
  - [ ] Configure CI to run component evals
  - [ ] Fail PR on component eval failure
  - [ ] Add eval reporting
- [ ] 🟡 Add research smoke to CI
  - [ ] Configure nightly research smoke
  - [ ] Add secrets for smoke tests
  - [ ] Add optional PR smoke

### J.5 Efficiency Budgets
- [ ] 🔴 Implement budget enforcement
  - [ ] Define token budget thresholds
  - [ ] Define latency budget thresholds
  - [ ] Fail on regression > configured %
  - [ ] Add budget alerts

### J.6 Eval UI
- [ ] 🟡 Implement eval UI tab
  - [ ] Add eval results view
  - [ ] Add trend charts
  - [ ] Add comparison views
  - [ ] Add drill-down to failures

### J.7 Prompt Versioning
- [ ] 🔴 Implement prompt store
  - [ ] Create `prompts/` directory
  - [ ] Define prompt schema
  - [ ] Add versioning (dev/staging/prod tags)
  - [ ] Implement prompt loading
- [ ] 🔴 Implement prompt management
  - [ ] Add prompt validation
  - [ ] Add prompt comparison
  - [ ] Add prompt rollback

### J.8 Testing
- [ ] 🔴 Write eval infrastructure tests
  - [ ] Test component runner
  - [ ] Test e2e runner
  - [ ] Test macro aggregator
- [ ] 🔴 Write CI integration tests
  - [ ] Test CI configuration
  - [ ] Test budget enforcement

**Acceptance Criteria:**
- ✅ Component suite in CI
- ✅ Research/efficiency/trajectory evals functional
- ✅ Ops metrics integrated
- ✅ Eval UI functional
- ✅ Prompt versioning implemented

---

## Phase K — Web product (primary UX)

**Goal:** Implement web app with chat, research streaming, provider UI, vault browser, and API.

**See [UX_DESIGN.md](docs/UX_DESIGN.md) for detailed UI/UX specifications.**

### K.1 Web Framework
- [ ] 🔴 Choose web framework
  - [ ] Evaluate options (Next.js + React recommended)
  - [ ] Select framework
  - [ ] Add to dependencies
- [ ] 🔴 Implement web server
  - [ ] Create `src/web/`
  - [ ] Implement server setup
  - [ ] Implement middleware
  - [ ] Implement error handling
- [ ] 🔴 Implement ultra-smooth performance
  - [ ] Implement virtual scrolling for long lists
  - [ ] Optimize streaming with requestAnimationFrame
  - [ ] Implement code splitting
  - [ ] Add GPU-accelerated animations
  - [ ] Target 60fps scrolling

### K.2 Chat Interface
- [ ] 🔴 Implement chat UI
  - [ ] Create chat interface
  - [ ] Implement message streaming
  - [ ] Add tool usage display
  - [ ] Add vault retrieval display
- [ ] 🔴 Implement chat API
  - [ ] Create chat endpoint
  - [ ] Implement streaming response
  - [ ] Add session management
  - [ ] Add history management

### K.3 Research Interface
- [ ] 🔴 Implement research UI
  - [ ] Create research interface
  - [ ] Implement progressive streaming
  - [ ] Add progress indicators
  - [ ] Add outline display
  - [ ] Add section streaming
- [ ] 🔴 Implement research API
  - [ ] Create research endpoint
  - [ ] Implement streaming response
  - [ ] Add run management
  - [ ] Add result storage

### K.4 Provider UI
- [ ] 🔴 Implement provider management UI
  - [ ] Create provider configuration UI
  - [ ] Implement `+` provider UI
  - [ ] Implement `+` model UI
  - [ ] Add provider testing
- [ ] 🔴 Implement provider API
  - [ ] Create provider endpoints
  - [ ] Implement CRUD operations
  - [ ] Add validation

### K.5 Vault Browser
- [ ] 🔴 Implement vault UI
  - [ ] Create vault browser
  - [ ] Implement vault search
  - [ ] Add note display
  - [ ] Add note editing
- [ ] 🔴 Implement vault API
  - [ ] Create vault endpoints
  - [ ] Implement search
  - [ ] Implement CRUD operations

### K.6 Run History
- [ ] 🔴 Implement history UI
  - [ ] Create run history view
  - [ ] Add run details
  - [ ] Add trace viewer
  - [ ] Add result download
- [ ] 🔴 Implement history API
  - [ ] Create history endpoints
  - [ ] Implement pagination
  - [ ] Implement filtering

### K.7 Export Functionality
- [ ] 🔴 Implement export options panel
  - [ ] Create export modal
  - [ ] Add format selection (MD, PDF, HTML)
  - [ ] Add export options (citations, metadata, math)
- [ ] 🔴 Implement Markdown export
  - [ ] Generate clean markdown
  - [ ] Add inline citations
  - [ ] Add source list
  - [ ] Preserve LaTeX math
  - [ ] Add YAML frontmatter metadata
- [ ] 🔴 Implement PDF export
  - [ ] Implement Puppeteer + HTML → PDF
  - [ ] Render HTML with MathJax
  - [ ] Add professional typesetting
  - [ ] Add cover page with metadata
  - [ ] Add table of contents
- [ ] 🔴 Implement HTML export
  - [ ] Generate single HTML file
  - [ ] Embed CSS
  - [ ] Add MathJax for math
  - [ ] Make responsive
  - [ ] Add interactive citations
- [ ] 🔴 Implement download experience
  - [ ] Add progress indicator
  - [ ] Add success state
  - [ ] Handle large file downloads
  - [ ] Add retry on failure
- [ ] 🟡 Implement batch export
  - [ ] Export multiple reports
  - [ ] Generate zip files
  - [ ] Export entire history
  - [ ] Add scheduled exports

### K.9 Cost Meter
- [ ] 🔴 Implement cost tracking UI
  - [ ] Create cost meter view
  - [ ] Add cost breakdown
  - [ ] Add cost trends
  - [ ] Add budget alerts
- [ ] 🔴 Implement cost API
  - [ ] Create cost endpoints
  - [ ] Implement aggregation
  - [ ] Implement budget checks

### K.10 Ops Metrics Integration
- [ ] 🔴 Integrate ops dashboard
  - [ ] Merge gateway metrics
  - [ ] Add engine metrics
  - [ ] Add research metrics
  - [ ] Implement unified dashboard

### K.12 Product API
- [ ] 🔴 Design API surface
  - [ ] Define API schema
  - [ ] Define authentication
  - [ ] Define rate limiting
- [ ] 🔴 Implement API endpoints
  - [ ] Implement chat API
  - [ ] Implement research API
  - [ ] Implement provider API
  - [ ] Implement vault API
  - [ ] Implement history API
  - [ ] Implement cost API
- [ ] 🔴 Add API documentation
  - [ ] Add OpenAPI spec
  - [ ] Add API docs UI
  - [ ] Add examples

### K.13 Testing
- [ ] 🔴 Write web tests
  - [ ] Test chat UI
  - [ ] Test research UI
  - [ ] Test provider UI
  - [ ] Test vault UI
- [ ] 🔴 Write API tests
  - [ ] Test chat API
  - [ ] Test research API
  - [ ] Test provider API
  - [ ] Test vault API
- [ ] 🔴 Write integration tests
  - [ ] Test end-to-end flows
  - [ ] Test streaming
  - [ ] Test error handling

**Acceptance Criteria:**
- ✅ Chat + research streaming functional
- ✅ Provider UI (`+` provider / `+` model) functional
- ✅ Vault browser, run history, cost meter functional
- ✅ Ops metrics merged
- ✅ Product API surface functional
- ✅ Export functionality (MD, PDF, HTML) with download
- ✅ Ultra-smooth scrolling (60fps) achieved
- ✅ Simple, intuitive interface

---

## Phase L — Mathematical output rendering

**Goal:** Implement MathJax/KaTeX integration for proper LaTeX/Unicode rendering.

### L.1 Math Rendering Engine
- [ ] 🔴 Choose rendering engine
  - [ ] Evaluate MathJax vs KaTeX
  - [ ] Select engine
  - [ ] Add to dependencies
- [ ] 🔴 Implement rendering
  - [ ] Create `src/rendering/math.py`
  - [ ] Implement LaTeX parsing
  - [ ] Implement LaTeX validation
  - [ ] Implement formula preprocessing
  - [ ] Implement sanitization

### L.2 Inline Math
- [ ] 🔴 Implement inline math rendering
  - [ ] Detect `$...$` patterns
  - [ ] Render inline formulas
  - [ ] Handle escaping
  - [ ] Add validation

### L.3 Block Math
- [ ] 🔴 Implement block math rendering
  - [ ] Detect `$$...$$` patterns
  - [ ] Render block formulas
  - [ ] Handle alignment
  - [ ] Add validation

### L.4 Symbol Enrichment
- [ ] 🟡 Implement constrained decoding
  - [ ] Integrate with gateway
  - [ ] Enforce consistent symbol output
  - [ ] Add symbol validation
- [ ] 🟡 Implement multi-modal integration
  - [ ] Add equation image support
  - [ ] Implement OCR for equations
  - [ ] Add to document parsers

### L.5 Export Formats
- [ ] 🔴 Implement HTML export
  - [ ] Add MathJax to HTML template
  - [ ] Render math in HTML
  - [ ] Add responsive design
- [ ] 🔴 Implement PDF export
  - [ ] Add LaTeX typesetting
  - [ ] Render math in PDF
  - [ ] Add page layout
- [ ] 🟡 Implement MathML export
  - [ ] Generate MathML output
  - [ ] Add accessibility features
  - [ ] Add screen reader support

### L.6 CLI Integration
- [ ] 🔴 Add math rendering to CLI
  - [ ] Render math in terminal
  - [ ] Use Unicode where possible
  - [ ] Add fallback for complex formulas
- [ ] 🔴 Add math rendering to research output
  - [ ] Render math in markdown
  - [ ] Preserve LaTeX syntax
  - [ ] Add rendering hints

### L.7 Web Integration
- [ ] 🔴 Add math rendering to web UI
  - [ ] Integrate MathJax/KaTeX
  - [ ] Render math in chat
  - [ ] Render math in research
  - [ ] Add math preview

### L.8 Testing
- [ ] 🔴 Write rendering tests
  - [ ] Test inline math
  - [ ] Test block math
  - [ ] Test LaTeX validation
  - [ ] Test sanitization
- [ ] 🔴 Write export tests
  - [ ] Test HTML export
  - [ ] Test PDF export
  - [ ] Test MathML export
- [ ] 🔴 Write integration tests
  - [ ] Test CLI integration
  - [ ] Test web integration

**Acceptance Criteria:**
- ✅ LaTeX syntax detected and validated
- ✅ Inline math (`$...$`) renders correctly
- ✅ Block math (`$$...$$`) renders correctly
- ✅ HTML export with MathJax functional
- ✅ PDF export with proper typesetting functional
- ✅ Accessibility features (MathML, screen reader) functional

---

## Cross-Phase Tasks

### Documentation
- [ ] 🟡 Update all docs as phases complete
- [ ] 🟡 Add examples for new features
- [ ] 🟡 Update tutorials
- [ ] 🟡 Add troubleshooting guides

### Performance
- [ ] 🟡 Performance profiling
- [ ] 🟡 Optimize bottlenecks
- [ ] 🟡 Add performance benchmarks
- [ ] 🟡 Implement caching strategies

### Security
- [ ] 🔴 Security audit
- [ ] 🔴 Implement rate limiting
- [ ] 🔴 Add input validation
- [ ] 🔴 Add output sanitization
- [ ] 🔴 Implement secrets management

### Deployment
- [ ] 🟡 Create deployment scripts
- [ ] 🟡 Add Docker support
- [ ] 🟡 Add monitoring
- [ ] 🟡 Add logging
- [ ] 🟡 Add backup/restore

### Community
- [ ] 🟡 Add contribution guidelines
- [ ] 🟡 Add issue templates
- [ ] 🟡 Add PR templates
- [ ] 🟡 Add code of conduct

---

## Tracking

- **Total Tasks:** [To be counted]
- **Completed:** [To be counted]
- **In Progress:** [To be counted]
- **Blocked:** [To be counted]

**Current Phase:** [Select active phase]

**Last Updated:** 2026-08-08
