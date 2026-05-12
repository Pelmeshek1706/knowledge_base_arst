# Release Plan

## Purpose

This file defines the Product Requirements release milestones, milestone scope, and exit criteria.

## When to read this

Read this when planning implementation order, checking milestone readiness, or updating MVP delivery sequencing.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Goals and scope](goals-and-scope.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Validation and acceptance](validation-and-acceptance.md)

## Source of truth

This file is authoritative for the Product Requirements release plan.

## Content

## MVP Milestone 1 — Schemas + Config + Manifest

### Purpose

Establish the project foundation for schemas, configuration, manifest storage, hashing, and a basic CLI shell.

### Status

Planned.

### Depends on

- Product goals and MVP scope.
- Package/configuration requirements.

### Outputs

- Pydantic schemas.
- Config loader.
- Path handling.
- Manifest storage.
- Processed document storage skeleton.
- Hashing utilities.
- Basic CLI shell.

### In scope

- Pydantic schemas.
- Config loader.
- Path handling.
- Manifest storage.
- Processed document storage skeleton.
- Hashing utilities.
- Basic CLI shell.

### Out of scope

- Full parser implementation.
- Model processing.
- Neo4j graph sync.
- Retrieval and Q&A.

### Related docs

- [Functional requirements](functional-requirements.md)
- [Data and graph requirements](data-and-graph-requirements.md)

### Implementation checklist

- Implement config initialization.
- Implement manifest creation and update paths.
- Implement document scanning.
- Implement hashing utilities.
- Add basic CLI shell.

### Exit criteria

- Can initialize config and manifest.
- Can scan `data/` and create manifest entries.
- Can compute raw bytes and extracted text hashes where parser exists.

### Validation

- Verify config and manifest initialization.
- Verify recursive scan of `data/`.
- Verify hash computation for parser-supported files.

## MVP Milestone 2 — Local Parsing + Chunking

### Purpose

Convert supported local files into normalized raw text and chunks.

### Status

Planned.

### Depends on

- MVP Milestone 1.

### Outputs

- TXT parser.
- Markdown parser.
- PDF parser with `pdfplumber`.
- DOCX parser with `mammoth` and `python-docx` fallback.
- XLSX parser with `openpyxl`.
- Format-aware chunking.

### In scope

- TXT parser.
- Markdown parser.
- PDF parser with `pdfplumber`.
- DOCX parser with `mammoth` and `python-docx` fallback.
- XLSX parser with `openpyxl`.
- Format-aware chunking.

### Out of scope

- OCR for scanned PDFs.
- Model-based extraction.
- Neo4j sync.

### Related docs

- [Functional requirements](functional-requirements.md)
- [Data and graph requirements](data-and-graph-requirements.md)

### Implementation checklist

- Implement parsers for supported file types.
- Implement format-aware chunkers.
- Persist normalized raw text and chunks.

### Exit criteria

- Supported files convert into normalized raw text and chunks.

### Validation

- Test each supported file extension.
- Inspect sample chunks for source references and expected boundaries.

## MVP Milestone 3 — Local Model Processing

### Purpose

Add local model clients and structured extraction for summaries, tags, entities, and embeddings.

### Status

Planned.

### Depends on

- MVP Milestone 2.

### Outputs

- LM Studio LLM client.
- Local embedding client.
- Local reranker client.
- Structured extraction prompts.
- JSON validation and retries.

### In scope

- LM Studio LLM client.
- Local embedding client.
- Local reranker client.
- Structured extraction prompts.
- JSON validation and retries.

### Out of scope

- LLM-based canonicalization as an MVP requirement.
- External LLM APIs.

### Related docs

- [Functional requirements](functional-requirements.md)
- [Non-functional requirements](non-functional-requirements.md)

### Implementation checklist

- Implement local LLM client abstraction.
- Implement local embedding client.
- Implement local reranker client.
- Add structured extraction prompts.
- Add validation and retry handling for JSON outputs.

### Exit criteria

- Chunks have summaries, tags, entities, embeddings.
- Documents have aggregated summaries, tags, entities.

### Validation

- Validate schema-conforming extraction outputs.
- Verify embeddings are normalized and dimension `1024`.

## MVP Milestone 4 — Neo4j Sync

### Purpose

Create the Neo4j schema and sync processed JSON into graph/vector state.

### Status

Planned.

### Depends on

- MVP Milestone 3.

### Outputs

- `kb setup-db`.
- Constraints/indexes/vector index.
- Graph sync service.
- Idempotent upserts.

### In scope

- `kb setup-db`.
- Constraints/indexes/vector index.
- Graph sync service.
- Idempotent upserts.

### Out of scope

- APOC dependency.
- Parsing, LLM calls, or embedding generation inside graph sync.

### Related docs

- [Functional requirements](functional-requirements.md)
- [Data and graph requirements](data-and-graph-requirements.md)

### Implementation checklist

- Implement schema setup command.
- Implement graph sync service.
- Add idempotent upserts.
- Write sync status back to manifest.

### Exit criteria

- Processed JSON becomes graph nodes/relationships in Neo4j.

### Validation

- Verify Neo4j constraints/indexes/vector index are created without APOC.
- Verify graph sync is idempotent.
- Verify rebuild from JSON.

## MVP Milestone 5 — Search and Q&A

### Purpose

Implement hybrid retrieval and source-grounded Q&A.

### Status

Planned.

### Depends on

- MVP Milestone 4.

### Outputs

- Keyword/title search.
- Entity/tag search.
- Vector search.
- Graph expansion.
- Hybrid scoring.
- Reranking.
- `search_documents`.
- `answer_question`.

### In scope

- Keyword/title search.
- Entity/tag search.
- Vector search.
- Graph expansion.
- Hybrid scoring.
- Reranking.
- `search_documents`.
- `answer_question`.

### Out of scope

- Unsupported claims beyond retrieved context.
- External write actions.

### Related docs

- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Validation and acceptance](validation-and-acceptance.md)

### Implementation checklist

- Implement retrieval pipeline.
- Implement score breakdowns and configurable weights.
- Implement Q&A over retrieved chunks.
- Add source references and warnings.

### Exit criteria

- Benchmark retrieval and Q&A can be evaluated.

### Validation

- Run benchmark retrieval and Q&A cases.
- Verify expected documents are found in top-10.
- Verify source-grounded answers include source references.

## MVP Milestone 6 — Agent Tool Readiness

### Purpose

Expose stable read-only search/Q&A capabilities through `KnowledgeToolService`, LangChain StructuredTools, and a minimal LangGraph `personal_kb` agent.

### Status

Planned.

### Depends on

- MVP Milestone 5.

### Outputs

- `KnowledgeToolService` facade.
- LangChain `StructuredTool` wrappers.
- Minimal LangGraph `personal_kb` agent orchestration.
- Stable structured JSON outputs.
- Tool schemas.
- Error handling.
- CLI `--json` output.

### In scope

- `KnowledgeToolService` facade.
- LangChain `StructuredTool` wrappers.
- Minimal LangGraph `personal_kb` agent orchestration.
- Stable structured JSON outputs.
- Tool schemas.
- Error handling.
- CLI `--json` output.

### Out of scope

- Business logic inside tool wrappers.
- External MCP adapter as the MVP internal path.
- Ingestion, rebuild, sync, setup-db, delete, move, rename, email, Confluence update, or Jira creation tools exposed to the MVP agent.

### Related docs

- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Users and stories](users-and-stories.md)

### Implementation checklist

- Implement `KnowledgeToolService`.
- Add StructuredTool wrappers.
- Add minimal LangGraph agent orchestration.
- Add stable tool schemas and error handling.
- Ensure CLI `--json` matches structured output contracts.

### Exit criteria

- LangGraph agent can call `search_documents` and `answer_question` through StructuredTools.
- Tools call core services directly and contain no business logic.
- Structured tool outputs match PRD schemas.
- External MCP adapter remains out of MVP internal path.

### Validation

- Verify LangGraph → StructuredTools → KnowledgeToolService → core services routing.
- Verify StructuredTools are thin wrappers.
- Verify no unsafe tools are exposed to the MVP agent.

## Future Milestone — MCP Adapter

### Purpose

Expose the same stable core search/Q&A capabilities to external MCP-compatible clients after MVP core tools are stable.

### Status

Future.

### Depends on

- MVP Milestone 6.
- Stable `KnowledgeToolService` contracts.

### Outputs

- MCP server adapter over `KnowledgeToolService`.
- Tool schema reuse with LangChain StructuredTools.
- External agent/client compatibility.
- Optional MCP clients for external document sources after local ingestion is stable.

### In scope

- MCP server adapter over `KnowledgeToolService`.
- Tool schema reuse with LangChain StructuredTools.
- External agent/client compatibility.
- Optional MCP clients for external document sources after local ingestion is stable.

### Out of scope

- MCP as the primary internal MVP agent path.
- Duplicated service logic or schemas.

### Related docs

- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Risks and future requirements](risks-and-future-requirements.md)

### Implementation checklist

- Implement MCP adapter over `KnowledgeToolService`.
- Reuse StructuredTool-compatible schemas.
- Add external client compatibility tests.

### Exit criteria

- External MCP-compatible client can call the same search/Q&A capabilities without duplicating service logic.

### Validation

- Verify MCP adapter reuses `KnowledgeToolService`.
- Verify MCP tools expose the same core capabilities as LangChain StructuredTools.

## Dependencies

- Product scope and goals.
- Functional requirements.
- Search/Q&A/CLI/agent requirements.
- Validation and acceptance criteria.

## Failure modes / risks

- Advancing to later milestones before foundational storage and parsing are stable can delay MVP.
- Adding MCP before core tools are stable creates premature complexity.
- Exposing unsafe tools to the MVP agent violates product requirements.

## Update rules

- Update this file when milestone order, scope, outputs, or exit criteria change.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when milestone exit criteria alter MVP acceptance.
- Update focused requirement files when a milestone scope change changes behavior.
