# MVP Implementation Order

## Purpose

This file preserves the MVP implementation order by repository area.

## When to read this

Read this when planning implementation sequence, deciding what to build next, or checking sprint acceptance criteria.

## Related files

- [index.md](index.md)
- [project-root-and-runtime-data.md](project-root-and-runtime-data.md)
- [core-schemas-storage.md](core-schemas-storage.md)
- [ingestion-parsing-models.md](ingestion-parsing-models.md)
- [graph-retrieval-qa.md](graph-retrieval-qa.md)
- [tools-agent-adapters.md](tools-agent-adapters.md)
- [cli-evaluation-scripts-tests.md](cli-evaluation-scripts-tests.md)
- [../../roadmap/index.md](../../roadmap/index.md)

## Source of truth

This file is authoritative for the repository-area sprint order from the original repository-structure document. The detailed phase roadmap is owned by [../../roadmap/index.md](../../roadmap/index.md).

## Status

Draft v0.1 sequence preserved from the original repository-structure document.

## Depends on

- Root configuration files and package metadata.
- `personal_kb/core/` and `personal_kb/schemas/` foundations.
- Runtime data rules for `data/`, `kb_storage/`, and `benchmark/`.

## Outputs

- Ordered implementation areas.
- Acceptance checks for each sprint.
- Repository areas required for MVP completion.

## In scope

- Sprint order by repository area.
- Files or package areas to implement in each sprint.
- Acceptance checks from the original source document.

## Out of scope

- Detailed per-phase backlog.
- New architectural decisions.
- New behavior not present in the original repository-structure document.

## Content

### Sprint 1 - Foundation

Implement:

```text
configs/
personal_kb/core/
personal_kb/schemas/
personal_kb/storage/
personal_kb/cli/main.py
```

Acceptance:

```text
kb status
```

can load config and initialize/read manifest.

### Sprint 2 - Local Discovery + TXT/MD

Implement:

```text
personal_kb/parsers/text_parser.py
personal_kb/parsers/markdown_parser.py
personal_kb/chunking/text_chunker.py
personal_kb/chunking/markdown_chunker.py
personal_kb/ingestion/file_discovery.py
personal_kb/ingestion/ingestion_planner.py
```

Acceptance:

```text
kb ingest data
```

creates per-document JSON for TXT/MD.

### Sprint 3 - Model Clients + Extraction

Implement:

```text
personal_kb/models/
personal_kb/ingestion/extraction_service.py
personal_kb/ingestion/embedding_service.py
```

Acceptance:

Processed JSON contains:

```text
summary
tags
entities
embeddings
processing metadata
```

### Sprint 4 - Neo4j Setup + Graph Sync

Implement:

```text
personal_kb/graph/schema_manager.py
personal_kb/graph/graph_sync_service.py
personal_kb/graph/graph_service.py
personal_kb/graph/cypher/
```

Acceptance:

```text
kb setup-db
kb ingest data
```

creates Neo4j nodes and relationships.

### Sprint 5 - Retrieval + Search

Implement:

```text
personal_kb/retrieval/
personal_kb/tools/knowledge_tool_service.py
```

Acceptance:

```text
kb search "some topic" --json
```

returns ranked documents with confidence and source refs.

### Sprint 6 - Q&A + Agent Tools

Implement:

```text
personal_kb/qa/
personal_kb/tools/structured_tools.py
personal_kb/agent/
```

Acceptance:

```text
kb ask "question about a document" --json
```

returns answer, source documents, and supporting chunks.

### Sprint 7 - Additional Parsers + Evaluation

Implement:

```text
pdf_parser.py
docx_parser.py
xlsx_parser.py
evaluation/
benchmark/
```

Acceptance:

Benchmark returns retrieval metrics and Q&A diagnostics.

## Implementation checklist

- [ ] Implement Sprint 1 foundation files and `kb status`.
- [ ] Implement Sprint 2 TXT/MD discovery, parsing, chunking, and ingest JSON output.
- [ ] Implement Sprint 3 local model clients, extraction, embeddings, and processed JSON metadata.
- [ ] Implement Sprint 4 Neo4j schema setup, graph sync, and graph service.
- [ ] Implement Sprint 5 retrieval services and `KnowledgeToolService` search path.
- [ ] Implement Sprint 6 Q&A service, StructuredTools, and LangGraph agent.
- [ ] Implement Sprint 7 PDF/DOCX/XLSX support, evaluation modules, and benchmark cases.

## Exit criteria

- All sprint acceptance checks pass.
- Business logic remains in services, not CLI handlers, tools, LangGraph nodes, or adapters.
- Benchmark diagnostics exist for retrieval and Q&A.

## Validation

- Run the acceptance command listed under each completed sprint.
- Run unit and integration tests relevant to the sprint.
- Run benchmark evaluation after Sprint 7.

## Update rules

Update this file when sprint ordering, implementation scope, acceptance commands, or repository-area ownership changes. Update [../../roadmap/index.md](../../roadmap/index.md) for detailed roadmap phase changes.
