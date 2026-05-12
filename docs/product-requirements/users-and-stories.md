# Users and Stories

## Purpose

This file defines the target users, personas, user stories, priorities, and acceptance criteria for Personal KB.

## When to read this

Read this when validating user value, writing acceptance tests, or checking whether implementation behavior satisfies the PRD stories.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Goals and scope](goals-and-scope.md)
- [Validation and acceptance](validation-and-acceptance.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)

## Source of truth

This file is authoritative for Product Requirements personas and user stories.

## Content

## Target Users and Personas

### Primary Persona — Technical Knowledge Worker

**Profile:** Data scientist / ML engineer / researcher working with technical documents, project notes, reports, spreadsheets, tickets, and emails.

**Needs:** Fast document lookup, reliable source references, Q&A over document content, relationship discovery between documents.

**Interface:** CLI plus internal LangGraph agent tools first, MCP adapter second, Telegram bot later.

### Future Persona — Agent User

**Profile:** User interacts with an AI agent that can call Personal KB tools.

**Needs:** Agent should retrieve documents, answer questions, show related documents, and explain graph relationships through LangChain StructuredTools.

**Constraints:** Agent must not modify source files or run ingestion. MCP is not the primary internal MVP path.

## User Stories

### Ingestion

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-001 | As a user, I want to ingest all supported files from `data/` so that my documents become searchable. | P0 | Running `kb ingest data` processes supported files and writes per-document JSON into `kb_storage/documents/`. |
| US-002 | As a user, I want already processed files to be skipped so that repeated ingestion is fast. | P0 | If relative path and hashes match manifest, file is skipped. |
| US-003 | As a user, I want changed files to become new document versions so that previous versions are preserved. | P0 | Same path + changed hash creates a new `Document` and `NEWER_VERSION_OF` relation. |
| US-004 | As a user, I want exact duplicate files to be detected so that duplicate documents are visible. | P0 | Different path + same raw bytes hash creates separate `Document` node and `DUPLICATE_OF` edge. |
| US-005 | As a user, I want failed documents to remain visible in manifest so that failures can be debugged later. | P0 | Parser/model/sync errors create manifest entries with `status="failed"` and error message. |

### Search and Retrieval

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-006 | As a user, I want to ask “which document contains X?” and receive ranked documents. | P0 | `kb search "X"` returns document list with confidence, summary, tags, source references, and matched chunks. |
| US-007 | As a user, I want hybrid search to use graph, tags/entities, keyword, vector search, and reranker. | P0 | Retrieval pipeline supports configurable `search_plan` and score breakdown. |
| US-008 | As a user, I want related documents to be shown from graph relationships. | P1 | `kb related --doc-id <uuid>` returns related documents via shared tags/entities/type/version/duplicate relations. |
| US-009 | As a user, I want duplicate documents to be inspectable. | P1 | `kb duplicates` lists duplicate groups and canonical document candidates. |

### Q&A

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-010 | As a user, I want to ask a question about document content and get an answer grounded in chunks. | P0 | `kb ask "question"` returns answer, confidence, source documents, source references, and supporting chunks. |
| US-011 | As a user, I want supporting chunk text when the question is about document content. | P0 | Q&A response includes `supporting_chunks.text` for content questions. |
| US-012 | As a user, I want document lookup queries to return summaries and source refs, not full chunk text by default. | P1 | Document lookup output returns matched chunk summaries and source references unless full context is requested. |

### Agent/Tool Usage

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-013 | As an agent, I need structured JSON outputs so that I can call downstream tools reliably. | P0 | Search and Q&A tools return schema-valid JSON. |
| US-014 | As a product owner, I want the agent to have search-only access in MVP so that source data remains safe. | P0 | Agent tools exclude ingestion, rebuild, sync, delete, move, rename, send email, and external writes. |
| US-015 | As a product owner, I want the MVP agent to use LangGraph internally so that query routing can later become multi-step without rewriting retrieval logic. | P0 | MVP includes a LangGraph `personal_kb` agent that calls tool wrappers for search/Q&A. |
| US-016 | As an engineer, I want Personal KB capabilities exposed as LangChain StructuredTools so that tool schemas are explicit and reusable. | P0 | MVP tools are implemented as LangChain `StructuredTool` wrappers over `KnowledgeToolService`. |
| US-017 | As an engineer, I want tools to be thin wrappers so that business logic stays testable in core services. | P0 | Tool wrappers contain validation/call/return glue only; retrieval, Q&A, graph queries, reranking, and answer generation live in services. |
| US-018 | As a future external agent, I want MCP tools to expose the same capabilities after MVP so that external clients can reuse Personal KB. | P1 | MCP server adapter is documented as future work and reuses the same core services/contracts. |

## Dependencies

- Story acceptance criteria rely on detailed requirements in [functional-requirements.md](functional-requirements.md), [data-and-graph-requirements.md](data-and-graph-requirements.md), and [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md).
- MVP acceptance criteria are in [validation-and-acceptance.md](validation-and-acceptance.md).

## Failure modes / risks

- Agent tools that modify source files or run ingestion violate US-014 and the future persona constraints.
- Returning unstructured or schema-invalid outputs violates US-013.
- Search results without source references do not satisfy US-006 or US-010.

## Validation

- Convert each P0 story acceptance criterion into a test or manual release gate.
- Verify `kb search`, `kb ask`, `kb related`, and `kb duplicates` behavior against the relevant story rows.
- Verify agent tools expose only the safe search/Q&A capabilities allowed by the stories.

## Update rules

- Update this file when personas, story priorities, or story acceptance criteria change.
- Update focused requirement files when a story change alters system behavior.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when acceptance criteria change.
