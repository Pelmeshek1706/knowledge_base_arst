# Python Class Design Overview

## Purpose

This file defines the cross-cutting Python class design for the `personal_kb` MVP: scope, design goals, package layout, dependency direction, composition root, error model, testing strategy, implementation order, class responsibility matrix, acceptance criteria, and final implementation recommendation.

## When to read this

Read this before changing:

- Python package boundaries;
- dependency direction between services and adapters;
- composition root wiring;
- cross-layer error handling;
- class responsibility ownership;
- implementation order;
- MVP readiness criteria.

## Related files

- [index.md](index.md)
- [schemas.md](schemas.md)
- [core-storage-ingestion.md](core-storage-ingestion.md)
- [model-extraction-services.md](model-extraction-services.md)
- [graph-services.md](graph-services.md)
- [retrieval-services.md](retrieval-services.md)
- [qa-services.md](qa-services.md)
- [tool-services.md](tool-services.md)
- [agent-services.md](agent-services.md)
- [../index.md](../index.md)
- [../../architecture/index.md](../../architecture/index.md)

## Source of truth

This file is authoritative for cross-cutting class-design rules. Focused files are authoritative for their specific layer contracts.

## Content

### Document status

```text
Status: Draft v0.1
Project: personal_kb
Python: 3.11
Package manager: uv
CLI framework: argparse
Primary implementation target: schemas + config + manifest
Architecture baseline: Technical Architecture v0.3, PRD v0.2, Neo4j Graph Schema v0.1
```

### MVP purpose

The Python class design defines the implementation shape for a local-first document GraphRAG system that:

1. Processes local files from `data/`.
2. Stores processed state in `kb_storage/`.
3. Syncs graph/vector data into Neo4j.
4. Answers questions through an internal LangGraph agent.
5. Exposes capabilities as LangChain `StructuredTool` wrappers.
6. Keeps tools as thin wrappers over core Python services.

Required MVP execution path:

```text
User
-> LangGraph personal_kb agent
-> LangChain StructuredTools
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService
-> Neo4j + kb_storage + local models
```

The MCP server adapter is not part of the primary MVP internal path. It will be added later and must reuse the same core services and schemas.

### Design goals

| Goal | Description |
|---|---|
| Testability | Business logic lives in services, not tools or CLI handlers. |
| Portability | Same services can be called from CLI, LangGraph tools, future MCP, API, or Telegram bot. |
| Local-first execution | LLM via LM Studio, embeddings/reranker via local `transformers` / `sentence-transformers`. |
| Rebuildable state | `kb_storage` is primary processed storage; Neo4j can be rebuilt from JSON. |
| Clear boundaries | Parsing, chunking, extraction, graph sync, retrieval, scoring, and Q&A are separate components. |
| MVP simplicity | No APOC, no external write actions, no OCR, no multi-user permissions. |
| Future extensibility | Leave clean extension points for MCP, Confluence, Jira, Gmail, FAQ memory, UI. |

### Non-goals

The following are not part of the MVP class design:

- Web API implementation.
- Telegram bot implementation.
- MCP server implementation as the primary path.
- External source ingestion from Confluence/Jira/Gmail/Google Drive.
- OCR for scanned PDFs.
- LLM-inferred document relationship generation as a required step.
- File move/rename/delete actions.
- Sending emails or updating external systems.
- Production multi-user access control.

### Proposed package structure

```text
personal_kb/
  __init__.py

  cli/
    __init__.py
    main.py
    commands.py
    formatters.py

  core/
    __init__.py
    config_loader.py
    hashing.py
    ids.py
    logging.py
    normalization.py
    paths.py
    time.py
    errors.py

  schemas/
    __init__.py
    common.py
    config.py
    document.py
    chunk.py
    entity.py
    tag.py
    manifest.py
    processing.py
    relationships.py
    search.py
    qa.py
    tools.py
    graph.py

  storage/
    __init__.py
    manifest_store.py
    processed_document_store.py
    json_store.py

  parsers/
    __init__.py
    base.py
    pdf_parser.py
    docx_parser.py
    markdown_parser.py
    txt_parser.py
    xlsx_parser.py
    registry.py

  chunking/
    __init__.py
    base.py
    pdf_chunker.py
    docx_chunker.py
    markdown_chunker.py
    txt_chunker.py
    xlsx_chunker.py
    registry.py

  models/
    __init__.py
    llm_client.py
    embedding_client.py
    reranker_client.py
    extraction_client.py

  extraction/
    __init__.py
    prompts.py
    structured_extractor.py
    aggregation.py

  graph/
    __init__.py
    neo4j_driver.py
    schema_manager.py
    graph_service.py
    graph_sync_service.py
    cypher_templates.py

  ingestion/
    __init__.py
    file_discovery.py
    ingestion_service.py
    processing_planner.py
    duplicate_detector.py

  retrieval/
    __init__.py
    retrieval_service.py
    keyword_search.py
    entity_search.py
    tag_search.py
    vector_search.py
    graph_expansion.py
    scoring.py

  qa/
    __init__.py
    qa_service.py
    answer_generator.py
    context_builder.py

  tools/
    __init__.py
    knowledge_tool_service.py
    langchain_tools.py
    tool_registry.py

  agents/
    __init__.py
    state.py
    router.py
    langgraph_agent.py

  evaluation/
    __init__.py
    benchmark_loader.py
    retrieval_metrics.py
    qa_metrics.py
    evaluator.py

  adapters/
    __init__.py
    mcp/
      __init__.py
      server.py        # future, not MVP primary path

configs/
  config.yaml

data/
  .gitkeep

kb_storage/
  manifest.json
  documents/
  logs/

benchmark/
  benchmark.jsonl

scripts/
  setup_neo4j.py

pyproject.toml
README.md
```

### Dependency direction

Allowed dependency direction:

```text
CLI / LangGraph / LangChain Tools / future MCP
-> KnowledgeToolService
-> Domain services
-> Repositories / Stores / Model clients / Graph client
-> External systems: filesystem, Neo4j, local model runtime
```

Forbidden dependency direction:

```text
GraphService -> CLI
RetrievalService -> LangGraph
QAService -> LangChain StructuredTool
Parser -> Neo4j
GraphSyncService -> LLM calls
Tool wrapper -> Cypher business logic
```

Main rule:

```text
Framework adapters depend on core services.
Core services do not depend on framework adapters.
```

### Composition root

A single composition function should wire dependencies.

**File:** `core/app_factory.py` or `main_factory.py`

```python
def build_app(config: PersonalKBConfig) -> PersonalKBApp:
    path_resolver = PathResolver(...)
    manifest_store = ManifestStore(...)
    processed_store = ProcessedDocumentStore(...)

    graph_driver = Neo4jDriverProvider(config.neo4j)
    schema_manager = Neo4jSchemaManager(graph_driver, config.neo4j)
    graph_service = GraphService(graph_driver, config.neo4j)

    llm_client = LLMClient(config.llm)
    embedding_client = EmbeddingClient(config.embedding)
    reranker_client = RerankerClient(config.reranker)

    extractor = StructuredExtractor(llm_client, NormalizationService())

    ingestion_service = IngestionService(...)
    retrieval_service = RetrievalService(...)
    qa_service = QAService(...)
    tool_service = KnowledgeToolService(...)

    langchain_tools = LangChainToolFactory(tool_service).create_tools()
    agent = PersonalKBLangGraphAgent(langchain_tools, QueryRouter())

    return PersonalKBApp(
        config=config,
        ingestion_service=ingestion_service,
        schema_manager=schema_manager,
        tool_service=tool_service,
        agent=agent,
    )
```

Avoid hidden global singletons.

### Error model

**File:** `core/errors.py`

```python
class PersonalKBError(Exception): ...
class ConfigError(PersonalKBError): ...
class ManifestError(PersonalKBError): ...
class ParserError(PersonalKBError): ...
class ChunkingError(PersonalKBError): ...
class ExtractionError(PersonalKBError): ...
class EmbeddingError(PersonalKBError): ...
class RerankerError(PersonalKBError): ...
class GraphError(PersonalKBError): ...
class RetrievalError(PersonalKBError): ...
class QAError(PersonalKBError): ...
```

Error handling policy:

| Layer | Behavior |
|---|---|
| Parser | raise parser-specific error, ingestion marks document failed |
| LLM extraction | retry, then mark failed if still invalid |
| Embedding | mark chunks as missing embedding if recoverable |
| Graph sync | keep JSON, set `neo4j_synced=false` |
| Retrieval | return warnings for partial fallback |
| Q&A | return missing_information/warnings instead of hallucinating |
| CLI | print readable error, return non-zero exit code |

### Testing strategy

Unit tests:

| Component | Tests |
|---|---|
| `ConfigLoader` | valid/invalid YAML, env resolution |
| `HashingService` | stable hashes, changed content |
| `NormalizationService` | lowercase/trim/collapse spaces |
| `ManifestStore` | load/save/update/failed status |
| `ProcessedDocumentStore` | schema validation and roundtrip |
| Parsers | file-specific extraction smoke tests |
| Chunkers | source_ref correctness |
| `ProcessingPlanner` | skip/version/duplicate/new cases |
| `ScoringService` | formula correctness |
| Tool wrappers | call `KnowledgeToolService`, no business logic |

Integration tests:

| Test | Expected result |
|---|---|
| ingest TXT/MD document | JSON + manifest created |
| graph sync from JSON | Neo4j nodes/relationships created |
| search by tag/entity | expected document returned |
| vector search | expected chunk returned |
| answer question | grounded answer + source refs |
| duplicate file | separate Document + `DUPLICATE_OF` |
| changed file | new Document + `NEWER_VERSION_OF` |

Benchmark tests use `benchmark/benchmark.jsonl` with 15-20 cases initially.

Metrics:

```text
Recall@K
Precision@K
MRR
Hit Rate
nDCG@K
answer faithfulness
citation correctness
latency
```

### Recommended implementation order

Phase 1 - Contracts and storage:

1. Create package skeleton.
2. Add `pyproject.toml` with `uv`.
3. Add Pydantic schemas.
4. Add config loader.
5. Add path resolver.
6. Add hashing service.
7. Add manifest store.
8. Add processed document store.

Phase 2 - Minimal ingestion without LLM:

9. Add TXT/MD parsers.
10. Add TXT/MD chunkers.
11. Add processing planner.
12. Save processed JSON without summaries/entities first.
13. Add failed-document handling.

Phase 3 - Neo4j schema and sync:

14. Add Neo4j driver provider.
15. Add `kb setup-db`.
16. Add graph sync from processed JSON.
17. Validate nodes/relationships in Neo4j.

Phase 4 - Local models:

18. Add embedding client.
19. Store embeddings in JSON and Neo4j.
20. Add LLM extraction client.
21. Add chunk/document extraction.
22. Add reranker client.

Phase 5 - Retrieval and Q&A:

23. Add keyword/entity/tag search.
24. Add vector search.
25. Add graph expansion.
26. Add hybrid scoring.
27. Add `search_documents`.
28. Add `answer_question`.

Phase 6 - Tools and agent:

29. Add `KnowledgeToolService`.
30. Add LangChain StructuredTools.
31. Add minimal LangGraph agent.
32. Add CLI search/ask through tool service.
33. Add benchmark evaluation.

Phase 7 - File format expansion:

34. Add PDF parser/chunker.
35. Add DOCX parser/chunker.
36. Add XLSX parser/chunker.
37. Improve chunking/scoring based on benchmark.

### Class responsibility matrix

| Class | Layer | Responsibility | Should not do |
|---|---|---|---|
| `ConfigLoader` | core | load/validate config | create services |
| `HashingService` | core | file/text hashing | parse files |
| `ManifestStore` | storage | manifest persistence | parse/sync graph |
| `ProcessedDocumentStore` | storage | processed JSON persistence | mutate Neo4j |
| `ParserRegistry` | parsers | choose parser | parse itself |
| `PdfParser` | parsers | PDF text extraction | chunk/LLM/embed |
| `BaseChunker` | chunking | split parsed content | extract entities |
| `StructuredExtractor` | extraction | LLM summaries/tags/entities | graph writes |
| `EmbeddingClient` | models | local embeddings | persistence |
| `RerankerClient` | models | local reranking | candidate retrieval |
| `ProcessingPlanner` | ingestion | decide skip/version/duplicate/new | process file content |
| `IngestionService` | ingestion | orchestrate ingestion | answer user questions |
| `Neo4jSchemaManager` | graph | setup indexes/constraints | sync documents |
| `GraphSyncService` | graph | JSON -> Neo4j | LLM/model calls |
| `GraphService` | graph | query graph | parse documents |
| `RetrievalService` | retrieval | search and rank | generate final answer |
| `QAService` | qa | answer with context | ingest files |
| `KnowledgeToolService` | tools | tool facade | implement low-level logic |
| `LangChainToolFactory` | tools | create StructuredTools | business logic |
| `PersonalKBLangGraphAgent` | agents | orchestrate tool calls | parse/sync/delete files |
| `CLIApp` | cli | command routing | business logic |

### MVP acceptance criteria

The class design is implementation-ready if:

1. Every core operation has a clear service owner.
2. All service inputs/outputs use Pydantic schemas.
3. CLI, LangChain tools, and future MCP can call the same core services.
4. Ingestion is deterministic and not agent-controlled.
5. LangGraph agent only calls allowed read/query tools.
6. Graph sync can rebuild Neo4j from `kb_storage` JSON.
7. Duplicate and version logic happens before expensive processing.
8. Failed documents stay in manifest with error messages.
9. No APOC-dependent class is required.
10. No external API is required for MVP.

### Final recommendation

Start implementation with:

```text
schemas -> config -> manifest -> processed JSON store
```

Do not start with LangGraph, Neo4j, or model code. Those layers depend on stable contracts.

The first code milestone should be:

```text
Given files in data/, personal_kb can:
1. load config,
2. scan files,
3. compute hashes,
4. decide skip/new/version/duplicate,
5. write manifest entries,
6. write a valid per-document JSON skeleton.
```

Only after that should Neo4j sync, model extraction, embeddings, retrieval, and LangGraph tools be added.

## Dependencies

This overview depends on the source architecture and requirements documents listed in the document status. It links to the focused class-design files for layer-specific contracts.

## Failure modes / risks

- Dependency direction can drift if adapters import domain implementation details or services import framework-specific types.
- Starting with LangGraph, Neo4j, or model code before schema/storage contracts can create unstable downstream contracts.
- Hidden global singletons can make local-first behavior harder to test and rebuild.
- Error handling must preserve failed documents in the manifest rather than losing processing state.

## Validation

- Check that each class in the responsibility matrix has one focused owner.
- Verify forbidden dependency directions are absent in implementation imports.
- Verify tests cover the unit, integration, and benchmark categories listed above.
- Confirm MVP acceptance criteria remain true after class or service changes.

## Update rules

Update this file when cross-cutting class design, dependency direction, package layout, composition wiring, error policy, testing strategy, implementation order, responsibility ownership, or acceptance criteria change.
