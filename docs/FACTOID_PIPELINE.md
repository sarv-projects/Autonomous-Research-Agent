# Factoid Extraction Pipeline

## Overview

The factoid extraction pipeline is a token optimization system that converts raw document chunks into structured JSON factoids, enabling efficient RAG with up to 90% token reduction while maintaining information quality.

## Motivation

Traditional RAG systems retrieve raw text chunks (500-800 tokens each) and feed them directly to LLMs. This approach has several problems:

1. **Token inefficiency** — Most tokens in a chunk are irrelevant to the specific query
2. **Context pollution** — Irrelevant information can distract the LLM
3. **Cost scaling** — Large contexts increase LLM costs quadratically
4. **Retrieval noise** — Similarity search on raw text often misses the key information

The factoid pipeline addresses these by extracting structured, queryable information units (factoids) during ingestion, then performing retrieval on the compressed factoids instead of raw chunks.

## Architecture

```
Document
    ↓
Chunking (500-800 tokens)
    ↓
Factoid Extractor (local LLM)
    ↓
Structured JSON Factoids
    ↓
Vector Embedding (factoid-level)
    ↓
Vector Database (with metadata)
    ↓
Retrieval (on factoids)
    ↓
Context Reconstruction (for Synthesizer)
```

## Factoid Schema

```python
from typing import Literal
from pydantic import BaseModel

class Factoid(BaseModel):
    """Structured information unit extracted from documents."""
    
    # Unique identifier
    id: str
    
    # Type of factoid
    type: Literal[
        "entity",        # Named entity (person, org, location)
        "relation",      # Relationship between entities
        "event",         # Temporal event with participants
        "statistic",     # Numerical data with context
        "definition",    # Concept definition
        "citation",      # Reference to another source
        "claim",         # Factual claim with attribution
        "methodology"    # Research method or process
    ]
    
    # Core content
    value: str
    
    # Confidence score (0-1)
    confidence: float
    
    # Source reference
    source: str
    chunk_id: str
    document_id: str
    
    # Metadata for filtering
    metadata: dict = {
        "entities": list[str],      # Entities mentioned
        "dates": list[str],         # Dates mentioned
        "numbers": list[float],     # Numbers mentioned
        "topics": list[str],        # Topic tags
    }
    
    # Cross-references
    related_factoids: list[str] = []  # IDs of related factoids
```

## Factoid Types

### Entity
Captures named entities with attributes.

```json
{
  "type": "entity",
  "value": "Einstein proposed the theory of relativity in 1905",
  "confidence": 0.95,
  "metadata": {
    "entities": ["Einstein"],
    "dates": ["1905"],
    "topics": ["physics", "relativity"]
  }
}
```

### Relation
Captures relationships between entities.

```json
{
  "type": "relation",
  "value": "Einstein developed relativity theory",
  "confidence": 0.92,
  "metadata": {
    "entities": ["Einstein", "relativity theory"],
    "relation_type": "developed"
  }
}
```

### Event
Captures temporal events with participants.

```json
{
  "type": "event",
  "value": "The 1905 annus mirabilis papers were published by Einstein",
  "confidence": 0.98,
  "metadata": {
    "entities": ["Einstein"],
    "dates": ["1905"],
    "event_type": "publication"
  }
}
```

### Statistic
Captures numerical data with context.

```json
{
  "type": "statistic",
  "value": "The speed of light is approximately 299,792,458 m/s",
  "confidence": 0.99,
  "metadata": {
    "numbers": [299792458],
    "units": "m/s",
    "topic": "physics"
  }
}
```

### Definition
Captures concept definitions.

```json
{
  "type": "definition",
  "value": "Relativity theory describes the relationship between space and time",
  "confidence": 0.94,
  "metadata": {
    "concepts": ["relativity theory", "space", "time"],
    "topic": "physics"
  }
}
```

### Citation
Captures references to other sources.

```json
{
  "type": "citation",
  "value": "According to Smith et al. (2020)...",
  "confidence": 0.97,
  "metadata": {
    "authors": ["Smith"],
    "year": "2020",
    "citation_type": "academic"
  }
}
```

## Factoid Extractor Agent

### Configuration

| Setting | Value |
|---------|--------|
| Provider | Local inference (vLLM/Ollama) |
| Models | Llama 3 8B, Phi-3, or similar |
| Hardware | CPU (slow) or GPU (fast) |
| Invoke when | Document ingestion, chunk processing |
| Do not invoke | Real-time queries (use cached factoids) |

### System Prompt

```
You are a factoid extraction specialist. Your task is to extract structured information units (factoids) from the provided text chunk.

For each factoid:
1. Identify the type (entity, relation, event, statistic, definition, citation, claim, methodology)
2. Extract the core value (concise, self-contained statement)
3. Assign a confidence score (0-1) based on clarity and source reliability
4. Extract relevant metadata (entities, dates, numbers, topics)
5. Identify related factoids (cross-references)

Rules:
- Extract only factual information, not opinions or speculation
- Preserve numerical precision and units
- Include source context for citations
- Be concise but complete
- Assign lower confidence to ambiguous or speculative claims
- Identify relationships between factoids when possible

Output format: JSON array of factoid objects following the schema.
```

### Implementation

```python
# src/rag/factoid/extractor.py

from typing import list
from pydantic import BaseModel
from ..local_inference import LocalLLM

class FactoidExtractor:
    def __init__(self, model: str = "llama3:8b"):
        self.llm = LocalLLM(model=model)
        self.system_prompt = """..."""  # System prompt above
    
    async def extract_factoids(
        self,
        chunk: str,
        chunk_id: str,
        document_id: str,
        source: str
    ) -> list[Factoid]:
        """Extract factoids from a text chunk."""
        
        prompt = f"""
        Extract factoids from the following text chunk:
        
        Chunk ID: {chunk_id}
        Document ID: {document_id}
        Source: {source}
        
        Text:
        {chunk}
        
        Output: JSON array of factoids.
        """
        
        response = await self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=prompt,
            response_format="json"
        )
        
        factoids = [Factoid(**item) for item in response]
        
        # Add source metadata
        for factoid in factoids:
            factoid.chunk_id = chunk_id
            factoid.document_id = document_id
            factoid.source = source
        
        return factoids
```

## Storage and Retrieval

### Storage

Factoids are stored in the vector database with both:

1. **Semantic embedding** — Embed the factoid `value` for semantic search
2. **Metadata filters** — Store structured metadata for exact filtering

```python
# src/rag/factoid/store.py

class FactoidStore:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    async def upsert_factoids(self, factoids: list[Factoid]) -> None:
        """Store factoids in vector database."""
        
        chunks = []
        for factoid in factoids:
            embedding = await self.embed_factoid(factoid.value)
            chunks.append(Chunk(
                id=factoid.id,
                text=factoid.value,
                embedding=embedding,
                metadata={
                    "type": factoid.type,
                    "confidence": factoid.confidence,
                    "source": factoid.source,
                    "chunk_id": factoid.chunk_id,
                    "document_id": factoid.document_id,
                    **factoid.metadata
                }
            ))
        
        await self.vector_store.upsert(chunks)
```

### Retrieval

Retrieval operates on factoids, not raw chunks:

```python
# src/rag/factoid/retrieve.py

class FactoidRetriever:
    def __init__(self, factoid_store: FactoidStore):
        self.store = factoid_store
    
    async def retrieve(
        self,
        query: str,
        k: int = 10,
        filters: dict | None = None
    ) -> list[Factoid]:
        """Retrieve relevant factoids for a query."""
        
        query_embedding = await self.embed_query(query)
        
        scored_chunks = await self.store.hybrid_query(
            text=query,
            embedding=query_embedding,
            k=k,
            filters=filters
        )
        
        # Convert back to Factoid objects
        factoids = [
            Factoid(
                id=chunk.id,
                type=chunk.metadata["type"],
                value=chunk.text,
                confidence=chunk.metadata["confidence"],
                source=chunk.metadata["source"],
                chunk_id=chunk.metadata["chunk_id"],
                document_id=chunk.metadata["document_id"],
                metadata={
                    k: v for k, v in chunk.metadata.items()
                    if k not in ["type", "confidence", "source", "chunk_id", "document_id"]
                }
            )
            for chunk in scored_chunks
        ]
        
        return factoids
```

## Context Reconstruction

The Synthesizer agent reconstructs context from retrieved factoids:

```python
# src/engine/agents/synthesizer.py

class SynthesizerAgent:
    async def synthesize_section(
        self,
        section_outline: str,
        retrieved_factoids: list[Factoid]
    ) -> str:
        """Synthesize a section from retrieved factoids."""
        
        # Group factoids by type for structured reconstruction
        factoids_by_type = {}
        for factoid in retrieved_factoids:
            if factoid.type not in factoids_by_type:
                factoids_by_type[factoid.type] = []
            factoids_by_type[factoid.type].append(factoid)
        
        # Build context from factoids
        context_parts = []
        
        # Add definitions first
        if "definition" in factoids_by_type:
            context_parts.append(
                "Key definitions:\n" + "\n".join([
                    f"- {f.value}" for f in factoids_by_type["definition"]
                ])
            )
        
        # Add statistics
        if "statistic" in factoids_by_type:
            context_parts.append(
                "Key statistics:\n" + "\n".join([
                    f"- {f.value}" for f in factoids_by_type["statistic"]
                ])
            )
        
        # Add events chronologically
        if "event" in factoids_by_type:
            context_parts.append(
                "Key events:\n" + "\n".join([
                    f"- {f.value}" for f in factoids_by_type["event"]
                ])
            )
        
        # Add relations and entities
        if "relation" in factoids_by_type:
            context_parts.append(
                "Key relationships:\n" + "\n".join([
                    f"- {f.value}" for f in factoids_by_type["relation"]
                ])
            )
        
        context = "\n\n".join(context_parts)
        
        # Generate section with reconstructed context
        prompt = f"""
        Write the following section based on the provided factoids:
        
        Section outline: {section_outline}
        
        Factoids:
        {context}
        
        Write a coherent, well-structured section that integrates these factoids.
        Maintain factual accuracy and cite sources where appropriate.
        """
        
        section = await self.llm.generate(prompt)
        
        return section
```

## Gap-Aware Evidence Assembly (AdaGATE)

The factoid pipeline implements gap-aware evidence assembly to ensure comprehensive coverage:

```python
# src/rag/factoid/gap_aware.py

class GapAwareAssembler:
    """Identify and fill information gaps in retrieved factoids."""
    
    async def identify_gaps(
        self,
        query: str,
        retrieved_factoids: list[Factoid],
        required_types: set[str]
    ) -> set[str]:
        """Identify missing factoid types."""
        
        present_types = {f.type for f in retrieved_factoids}
        missing_types = required_types - present_types
        
        return missing_types
    
    async def fill_gaps(
        self,
        query: str,
        missing_types: set[str],
        document_store: DocumentStore
    ) -> list[Factoid]:
        """Retrieve additional factoids to fill gaps."""
        
        additional_factoids = []
        
        for factoid_type in missing_types:
            # Generate targeted queries for missing types
            type_query = f"{query} {factoid_type}"
            
            # Retrieve with type filter
            type_factoids = await self.factoid_retriever.retrieve(
                query=type_query,
                k=5,
                filters={"type": factoid_type}
            )
            
            additional_factoids.extend(type_factoids)
        
        return additional_factoids
```

## Token Efficiency

### Baseline (Raw Chunks)

- Chunk size: 500-800 tokens
- Retrieval: top-10 chunks = 5,000-8,000 tokens
- Context fed to LLM: 5,000-8,000 tokens

### Factoid Pipeline

- Chunk size: 500-800 tokens
- Factoids per chunk: ~5-10 factoids
- Factoid size: ~50-100 tokens each
- Retrieval: top-10 factoids = 500-1,000 tokens
- Context fed to LLM: 500-1,000 tokens

### Savings

- **Token reduction**: 90% (5,000 → 500 tokens)
- **Cost reduction**: 90% (LLM costs scale with context)
- **Quality**: Maintained or improved (focused information)

## Integration with Research Pipeline

The factoid pipeline integrates into the research pipeline at the ingestion stage:

```
gather (raw documents)
    ↓
verify_sources (Retriever Guard)
    ↓
ingest (chunking)
    ↓
extract_factoids (Factoid Extractor) ← NEW
    ↓
store (vector database with factoids)
    ↓
retrieve (on factoids, not chunks) ← MODIFIED
    ↓
analyze (uses factoid context)
```

## Related Research

- **SARA** (Selective and Adaptive Retrieval-augmented Generation with Context Compression) — Adaptive context compression based on query relevance
- **CompactRAG** — Context compression techniques for efficient RAG
- **AdaGATE** — Gap-aware evidence assembly for comprehensive retrieval

## Configuration

```yaml
# config/factoid.yaml
factoid:
  extractor:
    model: "llama3:8b"
    provider: "ollama"
    gpu: true
    batch_size: 10
  
  schema:
    types:
      - entity
      - relation
      - event
      - statistic
      - definition
      - citation
      - claim
      - methodology
  
  retrieval:
    default_k: 10
    min_confidence: 0.7
    gap_aware: true
    required_types:
      - definition
      - statistic
  
  storage:
    backend: "lancedb"
    embedding_model: "text-embedding-3-small"
```

## Evaluation Metrics

### Token Efficiency

- Tokens per retrieved factoid vs raw chunk
- Total tokens per query
- Cost per query

### Quality

- Fact coverage (percentage of facts retrieved)
- Fact accuracy (factoid correctness vs source)
- Context reconstruction quality (BLEU/ROUGE vs original text)

### Performance

- Extraction latency (per chunk)
- Retrieval latency (per query)
- End-to-end latency (ingest to retrieve)

## Future Enhancements

1. **Incremental extraction** — Update factoids as documents change
2. **Factoid versioning** — Track factoid evolution over time
3. **Cross-document linking** — Link factoids across documents
4. **Confidence learning** — Improve confidence scoring with feedback
5. **Multi-modal factoids** — Extract factoids from images/tables
6. **Factoid summarization** — Generate higher-level factoid summaries
