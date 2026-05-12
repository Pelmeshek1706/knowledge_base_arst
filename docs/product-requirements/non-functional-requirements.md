# Non-Functional Requirements

## Purpose

This file defines cross-cutting quality, safety, privacy, determinism, testability, and portability requirements for Personal KB.

## When to read this

Read this when reviewing architecture, implementation quality, logging, privacy, configuration, rebuildability, or agent orchestration boundaries.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Goals and scope](goals-and-scope.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Risks and future requirements](risks-and-future-requirements.md)

## Source of truth

This file is authoritative for Product Requirements non-functional requirements NFR-001 through NFR-012.

## Content

| ID | Requirement | Target | Priority |
|---|---|---|---|
| NFR-001 | Local-first execution | No external LLM API required for MVP. | P0 |
| NFR-002 | Search latency | Document lookup and relationship retrieval should complete in ~10 seconds on initial dataset. | P0 |
| NFR-003 | Rebuildability | Neo4j graph must be rebuildable from JSON. | P0 |
| NFR-004 | Safety | Original source files must never be modified. | P0 |
| NFR-005 | Determinism | Ingestion decisions must be deterministic based on manifest, hashes, and config. | P0 |
| NFR-006 | Testability | Core logic must be testable without real LLM/Neo4j where possible. | P0 |
| NFR-007 | Observability | Ingestion/search must log key events and errors. | P1 |
| NFR-008 | Configurability | Model names, paths, search weights, and Neo4j connection must be configurable. | P0 |
| NFR-009 | Extensibility | Future sources must be able to normalize into the same RawDocument/ProcessedDocument model. | P1 |
| NFR-010 | Privacy | Sensitive document text should not be logged by default. | P0 |
| NFR-011 | Tool portability | The same core services must be callable from CLI, LangChain StructuredTools, and future MCP adapter. | P0 |
| NFR-012 | Orchestration isolation | LangGraph orchestration must not contain document processing, graph sync, or destructive operations. | P0 |

## Responsibility

These requirements constrain every implementation area rather than a single feature.

## Component boundaries

- Core logic must remain testable without real LLM/Neo4j where possible.
- LangGraph orchestration must not contain document processing, graph sync, or destructive operations.
- The same core services must be callable from CLI, LangChain StructuredTools, and the future MCP adapter.

## Data flow

- Ingestion decisions are deterministic from manifest, hashes, and config.
- Neo4j graph state is rebuildable from JSON.
- Sensitive document text is not logged by default.

## Design decisions

- MVP uses local-first execution with no external LLM API requirement.
- Search and relationship retrieval target ~10 seconds on the initial dataset.
- Model names, paths, search weights, and Neo4j connection must be configurable.

## Trade-offs

- Local-first execution improves privacy but depends on local model availability and performance.
- JSON rebuildability adds storage volume but avoids repeating expensive parsing/extraction/embedding work.
- Core-service portability constrains tool implementation but avoids duplicated behavior across CLI, LangChain StructuredTools, and future MCP.

## Dependencies

- Manifest and processed JSON storage.
- Neo4j graph/vector layer.
- Local LLM, embedding, and reranker clients.
- CLI, LangChain StructuredTools, and future MCP adapter.
- Logging configuration that avoids sensitive full-text output by default.

## Failure modes / risks

- Search latency above ~10 seconds harms usability.
- Logging sensitive document text creates a privacy risk.
- Business logic in orchestration or tools violates testability and portability.
- Non-deterministic ingestion decisions can create duplicate, skipped, or versioned document errors.
- Rebuildability breaks if Neo4j state depends on data not persisted in JSON.

## Risks and mitigations

- Use candidate pruning, top-k limits, and rerank only after narrowing candidates to mitigate search latency.
- Keep tools as thin wrappers over `KnowledgeToolService` to preserve testability and portability.
- Do not log full text by default to mitigate sensitive data exposure.
- Use manifest, hashes, and config for deterministic ingestion decisions.

## Validation

- Verify no external LLM API is required for MVP.
- Verify source files are never modified.
- Verify Neo4j can be rebuilt from JSON.
- Verify tests can cover core logic with fake LLM/Neo4j where possible.
- Verify logs avoid sensitive full text by default.
- Verify LangGraph orchestration excludes processing, sync, and destructive operations.

## Validation strategy

Use a combination of unit tests for deterministic decisions, integration tests for rebuildability, CLI/tool contract tests for portability, and log review for privacy.

## Update rules

- Update this file when cross-cutting quality, privacy, safety, determinism, or portability targets change.
- Update focused functional files when an NFR change alters specific behavior.
- Update [risks-and-future-requirements.md](risks-and-future-requirements.md) if an NFR introduces or changes a product risk.
