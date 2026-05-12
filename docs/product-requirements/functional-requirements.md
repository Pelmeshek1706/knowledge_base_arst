# Functional Requirements

## Purpose

This file defines the implementation-driving product requirements for project setup, ingestion, parsing, chunking, extraction, local models, processed storage, and graph sync.

## When to read this

Read this when implementing or changing ingestion, document processing, model execution, processed JSON storage, or Neo4j sync behavior.

## Related files

- [Product requirements index](index.md)
- [Goals and scope](goals-and-scope.md)
- [Data and graph requirements](data-and-graph-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Validation and acceptance](validation-and-acceptance.md)

## Source of truth

This file is authoritative for Product Requirements functional requirements FR-001 through FR-062.

## Content

## Project and Configuration

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | The package name must be `personal_kb`. | P0 |
| FR-002 | The project must use Python `3.11`. | P0 |
| FR-003 | The package manager must be `uv`. | P0 |
| FR-004 | The CLI must use `argparse`. | P0 |
| FR-005 | Configuration must be explicit and file-based. | P0 |
| FR-006 | Default document folder must be `data/`. | P0 |
| FR-007 | Default processed storage folder must be `kb_storage/`. | P0 |
| FR-008 | Default benchmark folder must be `benchmark/`. | P0 |
| FR-009 | File paths stored in JSON must be relative. | P0 |

## Neo4j Setup

| ID | Requirement | Priority |
|---|---|---|
| FR-010 | Neo4j URI must default to `bolt://localhost:7687`. | P0 |
| FR-011 | Neo4j database must default to `knowledge_base3`. | P0 |
| FR-012 | If `knowledge_base3` is unavailable, system should support fallback to `neo4j`. | P1 |
| FR-013 | APOC must not be required in MVP. | P0 |
| FR-014 | Main DB setup flow must be `kb setup-db`. | P0 |
| FR-015 | Optional auto setup mode may be exposed via `--auto-setup-db`. | P1 |
| FR-016 | `kb ingest` must automatically sync processed documents to Neo4j after successful processing. | P0 |

## File Discovery and Hashing

| ID | Requirement | Priority |
|---|---|---|
| FR-017 | System must scan `data/` recursively for supported file extensions. | P0 |
| FR-018 | System must ignore unsupported files with warning. | P1 |
| FR-019 | System must compute raw bytes hash using SHA-256. | P0 |
| FR-020 | System must compute extracted text hash using SHA-256 after parsing. | P0 |
| FR-021 | System must use manifest state to decide whether to skip, process, version, or mark duplicate. | P0 |

## Parsers

| ID | Requirement | Priority |
|---|---|---|
| FR-022 | PDF parser must use `pdfplumber` as primary parser. | P0 |
| FR-023 | PDF parser may use PyMuPDF as fallback when `pdfplumber` fails or extracts poor text. | P1 |
| FR-024 | DOCX parser must use `mammoth` as primary parser. | P0 |
| FR-025 | DOCX parser must use `python-docx` as fallback for raw paragraphs/tables. | P1 |
| FR-026 | XLSX parser must use `openpyxl`. | P0 |
| FR-027 | Markdown and TXT parsers may be built-in. | P0 |
| FR-028 | OCR for scanned PDFs must not be implemented in MVP. | P0 |

## Chunking

| ID | Requirement | Priority |
|---|---|---|
| FR-029 | PDF chunking must be page-aware. | P0 |
| FR-030 | DOCX chunking must be heading-aware where headings are detected. | P0 |
| FR-031 | Markdown chunking must preserve heading hierarchy. | P0 |
| FR-032 | TXT chunking must use fixed-size chunks with overlap. | P0 |
| FR-033 | XLSX chunking must treat workbook as Document, sheet as logical section/source_ref, table/range as Chunk. | P0 |
| FR-034 | Full chunk text must be stored for Q&A. | P0 |

## Extraction

| ID | Requirement | Priority |
|---|---|---|
| FR-035 | System must generate chunk summaries. | P0 |
| FR-036 | System must generate chunk tags. | P0 |
| FR-037 | System must extract chunk entities. | P0 |
| FR-038 | System must aggregate document-level summary, tags, entities, and entity summaries from chunks. | P0 |
| FR-039 | Tags and entities must include confidence field, even if `null` or `1.0`. | P0 |
| FR-040 | Tag/entity normalization must use lowercase + trim + collapse spaces in MVP. | P0 |
| FR-041 | LLM-based canonicalization is future-only. | P2 |

## Model Execution

| ID | Requirement | Priority |
|---|---|---|
| FR-042 | LLM must use LM Studio OpenAI-compatible endpoint at `http://localhost:1234/v1`. | P0 |
| FR-043 | LLM model must be configured as `mlx-community/Qwen3.5-9B-OptiQ-4bit`. | P0 |
| FR-044 | Embedding model must be `Qwen/Qwen3-Embedding-0.6B`. | P0 |
| FR-045 | Embedding dimension must be `1024`. | P0 |
| FR-046 | Embeddings must be normalized. | P0 |
| FR-047 | Embedding execution must use local `transformers` or `sentence-transformers`. | P0 |
| FR-048 | Reranker model must be `Qwen/Qwen3-Reranker-0.6B`. | P0 |
| FR-049 | Reranker execution must use local `transformers` or `sentence-transformers`. | P0 |
| FR-050 | Reranker must support `top_k_before_rerank = 50` and `top_k_after_rerank = 8`. | P0 |
| FR-051 | Model calls must be behind client abstractions, not embedded directly in ingestion/search logic. | P0 |

## Processed Storage

| ID | Requirement | Priority |
|---|---|---|
| FR-052 | JSON must be primary processed storage. | P0 |
| FR-053 | Storage layout must use `kb_storage/manifest.json` and `kb_storage/documents/<document_id>.json`. | P0 |
| FR-054 | Per-document JSON must store raw extracted text. | P0 |
| FR-055 | Per-document JSON must store chunks with full text, summaries, tags, entities, source refs, and embeddings. | P0 |
| FR-056 | Embeddings must be stored as full arrays in JSON. | P0 |
| FR-057 | Failed documents must remain in manifest with `status="failed"` and error message. | P0 |
| FR-058 | Neo4j must be rebuildable from processed JSON without repeating parsing/extraction/embedding. | P0 |

## Graph Sync

| ID | Requirement | Priority |
|---|---|---|
| FR-059 | Graph sync must read processed JSON and upsert Neo4j nodes/relationships. | P0 |
| FR-060 | Graph sync must be idempotent. | P0 |
| FR-061 | Graph sync must not parse files, call LLM, generate embeddings, or mutate source files. | P0 |
| FR-062 | Sync status must be written back to manifest. | P0 |

## Public API / Methods

This PRD file names required CLI commands and service boundaries but does not define Python method signatures. Relevant named interfaces include:

- `kb setup-db`
- `kb ingest data`
- `KnowledgeToolService`
- `RetrievalService`
- `QAService`
- `GraphService`

## Inputs

- Local documents under `data/`.
- Configuration files.
- Existing manifest state in `kb_storage/manifest.json`.
- Processed document JSON under `kb_storage/documents/<document_id>.json`.

## Outputs

- Manifest entries in `kb_storage/manifest.json`.
- Per-document processed JSON under `kb_storage/documents/<document_id>.json`.
- Neo4j nodes, relationships, constraints, indexes, and vector index.
- Sync status written back to the manifest.

## Side effects

- `kb ingest` writes processed JSON and manifest state.
- `kb ingest` automatically syncs successfully processed documents to Neo4j.
- `kb setup-db` creates required Neo4j schema elements.
- Graph sync upserts graph state and updates manifest sync status.

## Testing requirements

- Test skip/process/version/duplicate decisions from manifest and hashes.
- Test parser behavior for each supported extension.
- Test chunking behavior for PDF, DOCX, Markdown, TXT, and XLSX.
- Test failed documents remain visible in manifest with `status="failed"` and error message.
- Test Neo4j sync idempotency and rebuildability from processed JSON.
- Test model calls are behind client abstractions.

## What this must not do

- Must not require APOC for MVP.
- Must not implement OCR for scanned PDFs in MVP.
- Must not mutate original source files.
- Must not parse files, call LLM, or generate embeddings during graph sync.
- Must not place model calls directly in ingestion/search logic.
- Must not use LLM-based tag/entity canonicalization as an MVP requirement.

## Extension points

- PyMuPDF fallback for PDFs.
- `python-docx` fallback for DOCX raw paragraphs/tables.
- Optional `--auto-setup-db`.
- Future LLM-based canonicalization.
- Future external sources normalized into the same internal document contracts.

## Dependencies

- Python `3.11`
- `uv`
- `argparse`
- `pdfplumber`
- PyMuPDF fallback
- `mammoth`
- `python-docx`
- `openpyxl`
- `transformers` or `sentence-transformers`
- LM Studio OpenAI-compatible endpoint at `http://localhost:1234/v1`
- Neo4j at `bolt://localhost:7687`

## Failure modes / risks

- Unsupported files are ignored with warning.
- Parser/model/sync errors must create manifest entries with `status="failed"` and error message.
- Poor extraction quality weakens graph and search.
- Bad chunking harms retrieval and Q&A.
- Local model output instability can produce invalid JSON or hallucinated metadata.
- Neo4j schema drift can break graph sync.

## Validation

- Verify all FR-001 through FR-062 rows are covered by implementation, tests, or explicit backlog items.
- Verify processed JSON can rebuild Neo4j without repeating parsing, extraction, or embedding.
- Verify failed files remain visible in manifest.
- Verify original source files are never modified.

## Update rules

- Update this file when FR-001 through FR-062 change.
- Update [data-and-graph-requirements.md](data-and-graph-requirements.md) when storage or graph shapes change.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when requirement changes alter acceptance criteria.
- Update [release-plan.md](release-plan.md) when implementation sequencing changes.
