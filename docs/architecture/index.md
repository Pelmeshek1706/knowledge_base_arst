# Technical Architecture Index

## Purpose

This documentation folder defines the technical architecture source of truth for the `personal_kb` local-first GraphRAG system, including the focused Neo4j graph schema files split from `Neo4j_Graph_Schema_Personal_KB_v0.1.md`.

## When to read this

Start from this folder for:

- architecture updates;
- storage, ingestion, or graph schema changes;
- retrieval, Q&A, or scoring changes;
- agent, tool, CLI, or MCP-boundary changes;
- local model, embedding, reranker, or extraction changes;
- benchmark, validation, observability, security, or risk review.

## Source of truth

- [overview.md](overview.md) is authoritative for system goals, boundaries, core architectural decisions, assumptions, non-goals, global configuration, validation, security, risks, build order, and open questions.
- [storage-design.md](storage-design.md) is authoritative for local source handling, parsing, chunking, processed JSON, manifests, document identity, versioning, duplicates, ingestion flow, and file-type processing.
- [graph-schema.md](graph-schema.md) is authoritative for the high-level Neo4j graph schema purpose, MVP graph labels, MVP relationship types, naming conventions, and graph boundaries.
- [neo4j-node-schemas.md](neo4j-node-schemas.md) is authoritative for Neo4j node labels and node property contracts.
- [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md) is authoritative for Neo4j relationship contracts, directions, duplicate/version rules, and deterministic `RELATED_TO` behavior.
- [neo4j-indexes.md](neo4j-indexes.md) is authoritative for Neo4j constraints, standard indexes, full-text indexes, and vector index configuration.
- [neo4j-setup-sync.md](neo4j-setup-sync.md) is authoritative for `kb setup-db`, database fallback, no-APOC setup, and graph sync boundaries.
- [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md) is authoritative for idempotent Cypher upsert templates used by graph sync.
- [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md) is authoritative for Neo4j retrieval query templates and graph-backed score source mapping.
- [neo4j-future-extensions.md](neo4j-future-extensions.md) is authoritative for future graph labels and relationships that are not implemented in MVP.
- [neo4j-validation-risks.md](neo4j-validation-risks.md) is authoritative for Neo4j schema verification queries, acceptance criteria, and graph schema risks.
- [model-strategy.md](model-strategy.md) is authoritative for local LLM, embedding, reranker, extraction, normalization, document type classification, and model boundary rules.
- [retrieval-design.md](retrieval-design.md) is authoritative for search plans, retrieval layers, hybrid scoring, reranking, `search_documents` output, search logging, and retrieval validation.
- [qa-design.md](qa-design.md) is authoritative for query types, grounded answer generation, `answer_question` output, context policy, and Q&A validation.
- [agent-design.md](agent-design.md) is authoritative for LangGraph orchestration, LangChain `StructuredTool` wrappers, `KnowledgeToolService`, CLI commands, future MCP adapter boundaries, and agent safety limits.

## Reading order

1. Read [overview.md](overview.md) for the system summary and global constraints.
2. For Neo4j graph schema work, read [graph-schema.md](graph-schema.md) first, then the focused Neo4j file for the current task.
3. For non-graph architecture work, read the focused file related to the current task.
4. Read related files listed in the focused document.
5. Do not scan the whole folder unless explicitly requested.

## Files

| Topic | File | Purpose |
|---|---|---|
| Overview | [overview.md](overview.md) | Explains the high-level architecture, decisions, assumptions, non-goals, validation, security, risks, build order, and open questions. |
| Storage design | [storage-design.md](storage-design.md) | Defines `kb_storage`, processed JSON, manifests, ingestion, source parsing, chunking, identity, versioning, duplicates, and file-type handling. |
| Graph schema | [graph-schema.md](graph-schema.md) | Entry point for the Neo4j graph schema, MVP labels, MVP relationship types, naming conventions, and graph boundaries. |
| Neo4j node schemas | [neo4j-node-schemas.md](neo4j-node-schemas.md) | Defines `Document`, `Chunk`, `Tag`, `Entity`, and `DocumentType` node properties. |
| Neo4j relationship schemas | [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md) | Defines `CONTAINS`, `HAS_TAG`, `HAS_TYPE`, `MENTIONS`, `DUPLICATE_OF`, `NEWER_VERSION_OF`, and `RELATED_TO`. |
| Neo4j constraints and indexes | [neo4j-indexes.md](neo4j-indexes.md) | Defines constraints, standard indexes, full-text indexes, and the chunk vector index. |
| Neo4j setup and sync | [neo4j-setup-sync.md](neo4j-setup-sync.md) | Defines `kb setup-db`, database fallback, no-APOC setup, and graph sync boundaries. |
| Neo4j upserts | [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md) | Preserves idempotent Cypher upsert templates for graph sync. |
| Neo4j retrieval queries | [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md) | Defines graph retrieval query templates and score source mapping. |
| Neo4j future extensions | [neo4j-future-extensions.md](neo4j-future-extensions.md) | Lists future graph nodes and relationships that are not MVP scope. |
| Neo4j validation and risks | [neo4j-validation-risks.md](neo4j-validation-risks.md) | Defines verification queries, acceptance criteria, and graph schema risks. |
| Model strategy | [model-strategy.md](model-strategy.md) | Defines local LLM, embedding, reranker, extraction, normalization, and model boundary rules. |
| Retrieval design | [retrieval-design.md](retrieval-design.md) | Defines search planning, retrieval layers, scoring, reranking, search output, and retrieval failure handling. |
| Q&A design | [qa-design.md](qa-design.md) | Defines grounded answer generation, query types, answer output, context policy, and Q&A validation. |
| Agent design | [agent-design.md](agent-design.md) | Defines LangGraph, StructuredTools, `KnowledgeToolService`, CLI, future MCP adapter, and agent safety boundaries. |

## Update rules

- Update [overview.md](overview.md) when global architecture decisions, assumptions, non-goals, validation gates, security posture, risks, build order, or open questions change.
- Update [storage-design.md](storage-design.md) when source handling, parsing, chunking, manifests, processed JSON, identity, versioning, duplicate behavior, ingestion, or file-type processing changes.
- Update [graph-schema.md](graph-schema.md) when high-level Neo4j schema purpose, MVP graph labels, MVP relationship types, naming conventions, or graph boundaries change.
- Update [neo4j-node-schemas.md](neo4j-node-schemas.md) when Neo4j node labels, node properties, document type values, entity type handling, chunk source reference fields, or embedding storage rules change.
- Update [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md) when relationship types, directions, cardinality, properties, duplicate/version rules, or deterministic `RELATED_TO` logic change.
- Update [neo4j-indexes.md](neo4j-indexes.md) when constraints, lookup indexes, full-text indexes, vector index configuration, or embedding dimensions change.
- Update [neo4j-setup-sync.md](neo4j-setup-sync.md) when setup commands, database fallback behavior, no-APOC policy, setup ordering, graph sync boundaries, or sync side effects change.
- Update [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md) when `GraphSyncService` write methods, Cypher parameters, idempotency rules, or deterministic relationship ordering changes.
- Update [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md) when Neo4j retrieval query templates, index names, score source mapping, or query score storage rules change.
- Update [neo4j-future-extensions.md](neo4j-future-extensions.md) when future graph labels, future relationships, FAQ/QA memory design, external source node design, or LLM-inferred relationship policy changes.
- Update [neo4j-validation-risks.md](neo4j-validation-risks.md) when schema verification queries, MVP acceptance criteria, graph readiness checks, risks, mitigations, or validation gates change.
- Update [model-strategy.md](model-strategy.md) when model providers, model names, embedding dimensions, extraction behavior, normalization, or document type rules change.
- Update [retrieval-design.md](retrieval-design.md) when search plans, retrieval layers, scoring weights, reranking, search outputs, or search failure handling changes.
- Update [qa-design.md](qa-design.md) when grounded answer behavior, context return policy, citations, warnings, or Q&A validation changes.
- Update [agent-design.md](agent-design.md) when LangGraph flow, StructuredTool exposure, service boundaries, CLI commands, MCP boundaries, or agent write-action policy changes.
- Keep warnings, risks, validation requirements, and failure modes in the focused file that owns the behavior.

## Do not read everything by default

Coding agents should open only the focused files needed for the current task.
