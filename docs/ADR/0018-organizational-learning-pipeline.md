# ADR-0018: Organizational Learning Pipeline

**Status:** Approved
**Date:** 2026-07-24
**Owner:** AI & Domain Architect
**References:** ADR-0017 (4-Engine Architecture), ADR-0002 (Execution Over Learning), ADR-0007 (Single Knowledge Index), Product Bible §4 (Learning Engine)

---

## Context

ADR-0017 established the 4-Engine architecture. The Learning Engine's job: continuously learn from files, events, and user behavior to build organizational memory. This ADR defines the pipeline that powers it.

The pipeline ingests customer documents, extracts structured knowledge, builds a knowledge graph, generates embeddings, and makes everything queryable via RAG. All on-premise. No model training — HiveOS learns by reading, not by retraining.

V1 scope: file ingestion + parsing + knowledge graph + embeddings + basic RAG. Execution-history learning deferred to V2 per ADR-0002.

## Decision

### Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────┐    ┌────────┐
│  File Watch  │───▶│   Parser    │───▶│ Knowledge    │───▶│  Embeddings │───▶│   RAG   │───▶│ Memory │
│  & Ingest    │    │  & Extract  │    │ Graph Build  │    │  Index      │    │  Query  │    │ Store  │
└─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘    └─────────┘    └────────┘
       │                  │                  │                   │                │              │
       ▼                  ▼                  ▼                   ▼                ▼              ▼
   raw files        structured         entity/relation       vector +        retrieval     accumulated
   + metadata       chunks +           graph stored          keyword         over graph    org knowledge
                     metadata           in local DB           index           + chunks      for agents
```

### Stage 1: File Watch & Ingest

**Input:** Customer file system (watch folder + explicit upload).

| Aspect | Design |
|--------|--------|
| **Trigger** | Filesystem watcher (inotify/FSEvents) on configured directory. Periodic scan fallback. |
| **Supported formats** | PDF, DOCX, XLSX, CSV, TXT, MD, JSON, XML. V1: PDF + DOCX + CSV + XLSX. |
| **Metadata captured** | path, filename, size, mtime, mime type, SHA-256 hash, ingestion timestamp |
| **Deduplication** | SHA-256 hash check. Same hash = skip. Re-ingest only if mtime changes AND content hash differs. |
| **Queue** | Ingested files enter a processing queue (SQLite-backed, not external message broker). |
| **Privacy gate** | Before any processing: check file against exclusion rules (path patterns, filename patterns). Excluded files are logged but never parsed. |

**Storage:** Raw files stay in place. HiveOS never copies or moves customer files.

### Stage 2: Parser & Extractor

**Input:** Raw files from Stage 1.

| Aspect | Design |
|--------|--------|
| **PDF parsing** | PyMuPDF (fitz) for text + tables. Fallback: marker-pdf for complex layouts. |
| **DOCX parsing** | python-docx for structured extraction. Tables, headers, lists preserved. |
| **Spreadsheet** | openpyxl (XLSX) / csv (CSV). Row-oriented output with sheet name metadata. |
| **Chunking** | Recursive character splitter. Target chunk: 1000 chars, 200 overlap. Respect document boundaries (never split mid-sentence when avoidable). |
| **Metadata per chunk** | source_file, page_number, section_heading, chunk_index, chunk_type (text/table/header/list), language |
| **Table extraction** | Tables become separate chunks with type=table. Preserved as Markdown tables for LLM readability. |
| **OCR fallback** | For image-heavy PDFs: Tesseract OCR. Triggered when PyMuPDF extracts <50 chars per page. |

**Output:** `ParsedDocument` objects stored in local SQLite. Each contains chunks with metadata.

### Stage 3: Knowledge Graph Build

**Input:** Parsed chunks from Stage 2.

| Aspect | Design |
|--------|--------|
| **Entity extraction** | LLM-based extraction via configured provider. Prompt template: "Extract named entities and relationships from this text chunk." |
| **Entity types** | Person, Organization, Product, Location, Date, Metric, Concept, Document. Extensible per domain pack. |
| **Relation types** | works_for, mentions, related_to, contains, measures, created_on. Domain pack can define custom types. |
| **Storage** | SQLite with graph tables (nodes, edges, properties). Not a separate graph DB — keeps V1 simple. |
| **Chunk linking** | Each entity/relation links back to source chunk ID and source file. Enables traceability: "Where did this knowledge come from?" |
| **Conflict resolution** | Entity deduplication by fuzzy name match + type. "Acme Corp" and "ACME Corporation" → same node. Confidence score on each merge. |
| **Incremental build** | New files add to existing graph. Full rebuild available but not default. Graph is append-only with soft-delete for removed files. |
| **LLM calls** | Batch chunks (5-10 per call) to minimize API costs. Use local model (Ollama) when available, cloud when not. |

**Key design choice:** Knowledge graph is lightweight. It captures entities and relationships for retrieval, not a full ontological model. Domain packs can extend entity/relation types but the core graph stays simple.

### Stage 4: Embeddings Index

**Input:** Parsed chunks (Stage 2) + entity/relation descriptions (Stage 3).

| Aspect | Design |
|--------|--------|
| **Embedding model** | Local: sentence-transformers (all-MiniLM-L6-v2) via Ollama or direct. Cloud: provider's embedding API. Configurable. |
| **What gets embedded** | (1) Each text chunk. (2) Each entity description (name + context). (3) Each relation triple (subject-predicate-object as text). |
| **Vector store** | SQLite + sqlite-vec extension. No external vector DB dependency for V1. |
| **Index structure** | Two vectors per item: dense (embedding) + sparse (BM25 keyword). Enables hybrid search. |
| **Source tagging** | Every vector tagged with source type per ADR-0007: `org:` for customer files, `domain:` for domain pack content. |
| **Update strategy** | Re-embed only changed chunks (detected by chunk hash). Full re-index on demand. |
| **Dimension** | 384 (MiniLM default). Configurable for other models. |

**Why sqlite-vec:** Zero operational overhead. No separate vector DB service. Performance adequate for <1M vectors (typical V1 org). Migration path to Qdrant/pgvector in V2 if needed.

### Stage 5: RAG Query

**Input:** User/agent query.

| Aspect | Design |
|--------|--------|
| **Query processing** | Query → embedding + keyword extraction → hybrid search (dense + BM25) → rerank |
| **Retrieval modes** | (1) Semantic: vector similarity. (2) Keyword: BM25 exact match. (3) Graph: entity-neighbor traversal. (4) Hybrid: combined with RRF (Reciprocal Rank Fusion). |
| **Default mode** | Hybrid. Fallback to semantic-only if graph is sparse. |
| **Context assembly** | Top-K chunks (default K=5) + graph context (neighbors of detected entities) → assembled into prompt context. |
| **Source attribution** | Every retrieved chunk carries source file + page + section. RAG responses include citations. |
| **Confidence scoring** | Retrieval confidence based on: similarity score, source freshness, chunk quality. Below threshold → "I don't have enough information." |
| **Graph-augmented RAG** | When query mentions an entity found in KG, automatically expand context to include related entities and their source chunks. This is the KG's primary value-add over pure vector search. |
| **Token budget** | Respects configurable max context tokens. Prioritizes by relevance score when truncating. |

### Stage 6: Memory Store

**Input:** Accumulated knowledge from all prior stages.

| Aspect | Design |
|--------|--------|
| **What is memory** | Persistent, queryable organizational knowledge. Not conversation history. Not execution logs. The distilled understanding of the organization. |
| **Memory types** | (1) **Factual:** entities, relationships, metrics extracted from documents. (2) **Procedural:** workflows, processes discovered from documents. (3) **Temporal:** time-series data, trends, changes over time. (4) **Preferential:** user corrections, feedback on accuracy. |
| **Storage** | Same SQLite database as graph + embeddings. Single DB, multiple tables. |
| **Memory update triggers** | New file ingested, user correction, explicit memory command ("remember that X is Y"). |
| **Memory consolidation** | Periodic job: merge duplicate facts, update confidence scores, prune stale data (files deleted from watch folder). |
| **Agent access** | Agents query memory through the same RAG interface (Stage 5). Memory is not a separate API — it IS the knowledge graph + embeddings. |
| **Forgetting** | When source file is deleted from watch folder: soft-delete all derived knowledge. After configurable grace period (default 30 days): hard-delete. User can override. |

## Architecture Principles Applied

| Principle | Application |
|-----------|-------------|
| **Privacy-First** (ADR-0017) | All processing local. No data leaves infrastructure. Cloud LLM calls are optional and configurable. |
| **Single Knowledge Index** (ADR-0007) | All stages write to one SQLite DB. Source tagging separates domain vs org knowledge. |
| **On-Premise** (ADR-0008) | No external service dependencies. SQLite + local embeddings. Cloud LLM optional. |
| **Execution Over Learning** (ADR-0002) | V1 pipeline handles file-based learning. Execution-history learning (pattern detection) is V2 scope. |
| **Human Ownership of Truth** (ADR-0015) | Humans can correct memory. Confidence scores reflect data quality. System never claims certainty it doesn't have. |

## Technology Stack

| Component | V1 Choice | Rationale |
|-----------|-----------|-----------|
| File watcher | watchdog (Python) | Cross-platform, battle-tested |
| PDF parser | PyMuPDF + marker-pdf fallback | Speed + quality balance |
| LLM extraction | Configurable (Ollama local / cloud) | Privacy + flexibility |
| Embeddings | sentence-transformers / provider API | Local-first, cloud-optional |
| Vector store | sqlite-vec | Zero ops, adequate for V1 scale |
| Graph store | SQLite (graph tables) | Same DB, simple queries |
| Orchestration | LangGraph | Per Hermes integration, state machine suits pipeline |

## Consequences

**Positive:**
- Single SQLite database for all knowledge (graph + vectors + memory). One backup, one restore.
- No external service dependencies. Fully on-premise capable.
- Graph-augmented RAG gives better retrieval than pure vector search for entity-rich queries.
- Source tagging enables clean domain pack upgrades without touching org knowledge.
- Incremental processing avoids re-ingesting everything on new files.

**Negative:**
- SQLite limits V1 scale to ~1M vectors. Adequate for most SMBs but will need migration for large orgs.
- LLM-based entity extraction adds latency and cost per file. Mitigated by batch processing and local models.
- Knowledge graph is lightweight (not a full ontology). Complex reasoning over relationships is V2+ scope.
- Chunk quality directly impacts everything downstream. Bad parsing = bad knowledge. Mitigated by parser fallbacks and human review.

**Risks:**
- Entity deduplication accuracy depends on LLM quality. False merges create incorrect knowledge. Mitigation: confidence scores + human review for low-confidence merges.
- File encoding issues with non-Latin text (Persian, Arabic, CJK). Mitigation: encoding detection (chardet) + explicit encoding config per folder.

## V1 vs V2 Scope

| Capability | V1 | V2 |
|------------|----|----|
| File ingestion (watch folder) | Yes | Yes |
| PDF/DOCX/XLSX/CSV parsing | Yes | + all formats |
| Basic entity extraction | Yes | + relation extraction |
| SQLite graph + sqlite-vec | Yes | Migration to dedicated graph DB if needed |
| Hybrid RAG (semantic + keyword) | Yes | + graph traversal RAG |
| Memory consolidation | Basic (dedup + prune) | + pattern detection + trend analysis |
| Execution-history learning | No (ADR-0002) | Yes |
| Cross-file reasoning | Limited (entity neighbors) | Full graph reasoning |
| Auto-tagging / classification | No | Yes |
| User feedback loop | Manual correction | Active learning from corrections |

## References

- ADR-0017: Product Direction Update (4-Engine Architecture)
- ADR-0002: Execution Over Learning in V1
- ADR-0007: Single Knowledge Index with Source Tagging
- ADR-0008: On-Premise Default Deployment
- ADR-0015: Human Ownership of Business Truth
- Product Bible §4: Learning Engine
- Product Scope (doc 05): V1/V2 boundaries
