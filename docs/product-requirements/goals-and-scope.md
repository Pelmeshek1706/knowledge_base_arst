# Goals and Scope

## Purpose

This file defines the product goals, MVP non-goals, and MVP scope boundaries for Personal KB.

## When to read this

Read this before adding features, changing MVP boundaries, or deciding whether a behavior belongs in the MVP.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Risks and future requirements](risks-and-future-requirements.md)

## Source of truth

This file is authoritative for Product Requirements goals, MVP scope, and MVP non-goals.

## Content

## Product Goals

| Goal ID | Goal | Description | Priority |
|---|---|---|---|
| G1 | Local document ingestion | Process local PDF, DOCX, Markdown, TXT, and XLSX files from `data/`. | P0 |
| G2 | Structured processed storage | Persist processed document state in `kb_storage/` as rebuildable JSON. | P0 |
| G3 | Knowledge graph construction | Build Neo4j graph nodes and relationships for documents, chunks, entities, tags, document types, duplicates, and versions. | P0 |
| G4 | Hybrid document retrieval | Retrieve documents using graph, tag/entity, keyword, vector, and reranker-based search. | P0 |
| G5 | Source-grounded Q&A | Answer questions using supporting chunks and source references. | P0 |
| G6 | Internal LangGraph agent tools | Expose search/Q&A capabilities to the MVP agent through LangChain StructuredTools backed by core Python services. | P0 |
| G7 | No destructive source actions | Never rename, move, delete, or modify original files in MVP. | P0 |
| G8 | Local-first model execution | Use local LLM, embedding, and reranker models. | P0 |
| G9 | Benchmark-driven validation | Validate retrieval and Q&A with a benchmark dataset in `benchmark/`. | P1 |
| G10 | Future source extensibility | Preserve clean extension path for Confluence, Jira, Gmail, Google Docs/Sheets/Slides. | P1 |
| G11 | Future MCP compatibility | Add an MCP server adapter after MVP core tools are stable and keep MCP tools aligned with the same core service contracts. | P1 |

## Non-Goals for MVP

The MVP will not include:

- Web UI.
- Telegram bot.
- Real-time sync with Confluence, Jira, Gmail, or Google Drive.
- Write actions to external systems.
- File moving, renaming, deletion, or folder reorganization.
- Permission-aware multi-user access control.
- Scanned PDF OCR.
- FAQ/QA memory implementation.
- LLM-inferred document relationships as a required ingestion step.
- APOC dependency in Neo4j.
- Production-grade observability.
- MCP as the primary internal MVP agent path.

## MVP Scope

### In Scope

Supported local files:

```text
.pdf
.docx
.md
.txt
.xlsx
```

Default project folders:

```text
data/
kb_storage/
benchmark/
```

Supported actions:

- Initialize Neo4j schema with `kb setup-db`.
- Ingest local documents with `kb ingest data`.
- Parse documents.
- Compute raw bytes hash and extracted text hash.
- Detect exact duplicates.
- Detect changed files and create `NEWER_VERSION_OF` relations.
- Store failed documents in manifest with `status="failed"` and error message.
- Generate chunk-level and document-level summaries, tags, entities, and embeddings.
- Store full embeddings in per-document JSON.
- Sync processed JSON to Neo4j automatically during ingestion.
- Search documents.
- Ask source-grounded questions.
- Run MVP query orchestration through a LangGraph `personal_kb` agent.
- Expose MVP agent capabilities as LangChain `StructuredTool` wrappers.
- Route tools through `KnowledgeToolService` and core services, not business logic inside tools.
- Inspect related documents.
- Inspect duplicates.
- Return readable CLI output by default and structured JSON with `--json`.

### Out of Scope

Future but not MVP:

- Confluence/Jira/Gmail/Google Drive ingestion.
- Source-specific graph nodes for external systems.
- UI beyond CLI.
- OCR.
- Human approval workflows for external writes.
- FAQ memory.
- LLM-inferred relationship graph.
- Advanced tag/entity canonicalization via LLM.
- MCP server adapter as the primary MVP internal tool path.

## Dependencies

- Detailed ingestion and processing requirements are in [functional-requirements.md](functional-requirements.md).
- Query and agent requirements are in [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md).
- Future requirements are in [risks-and-future-requirements.md](risks-and-future-requirements.md).

## Failure modes / risks

- Adding out-of-scope behavior to MVP increases delivery risk.
- Destructive source-file actions violate P0 product goal G7.
- Treating MCP as the primary internal MVP agent path violates both the non-goals and out-of-scope list.
- Adding external connectors before local ingestion is stable conflicts with MVP scope.

## Validation

- Check planned work against the in-scope and out-of-scope lists before implementation.
- Verify P0 goals are covered by functional, data, graph, search, Q&A, CLI, and agent requirements.
- Confirm future work is tracked in [risks-and-future-requirements.md](risks-and-future-requirements.md), not silently promoted into MVP.

## Update rules

- Update this file when product goals, non-goals, supported file types, default folders, or MVP actions change.
- Update downstream focused requirements when a scope change affects behavior.
- Update [release-plan.md](release-plan.md) if scope changes alter milestone sequencing.
