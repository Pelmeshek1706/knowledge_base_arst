# Graph Services

## Purpose

This file defines the Neo4j-facing service classes for `personal_kb`: driver creation, schema setup, processed-document sync, and graph query methods used by retrieval and tool-facing services.

## When to read this

Read this when changing:

- Neo4j driver/database fallback behavior;
- `kb setup-db` schema setup;
- graph constraints, full-text indexes, or vector indexes;
- JSON-to-Neo4j sync behavior;
- graph query methods used by retrieval or tools;
- graph service prohibitions.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [core-storage-ingestion.md](core-storage-ingestion.md)
- [retrieval-services.md](retrieval-services.md)
- [tool-services.md](tool-services.md)
- [../../architecture/graph-schema.md](../../architecture/graph-schema.md)

## Source of truth

This file is authoritative for Neo4j driver, schema manager, graph sync, and graph query class design.

## Content

### `Neo4jDriverProvider`

**File:** `graph/neo4j_driver.py`

Responsibility:

- Create Neo4j driver.
- Handle database fallback from `knowledge_base3` to `neo4j`.
- Provide sessions.

```python
class Neo4jDriverProvider:
    def get_driver(self) -> Driver: ...
    def resolve_database(self) -> str: ...
```

### `Neo4jSchemaManager`

**File:** `graph/schema_manager.py`

Responsibility:

- Implement `kb setup-db`.
- Create constraints, full-text indexes, vector indexes.
- Avoid APOC.

```python
class Neo4jSchemaManager:
    def setup_schema(self) -> None: ...
    def check_schema(self) -> SchemaStatus: ...
```

MVP behavior:

```text
Primary: kb setup-db
Optional: kb ingest --auto-setup-db
Default kb ingest: check schema and fail clearly if missing
```

### `GraphSyncService`

**File:** `graph/graph_sync_service.py`

Responsibility:

- Read `ProcessedDocument`.
- Upsert Document, Chunk, Entity, Tag, DocumentType nodes.
- Upsert relationships.
- Store chunk embeddings in Neo4j vector property.
- Update manifest `neo4j_synced=true`.

```python
class GraphSyncService:
    def sync_document(self, processed_document: ProcessedDocument) -> GraphSyncResult: ...
    def sync_all_from_storage(self) -> GraphSyncRunResult: ...
```

Forbidden:

```text
No parsing.
No LLM calls.
No embedding generation.
No source file mutation.
```

### `GraphService`

**File:** `graph/graph_service.py`

Responsibility:

- Run graph queries.
- Fetch document/chunk/tag/entity relationships.
- Provide methods for retrieval services.

```python
class GraphService:
    def get_document(self, document_id: str) -> DocumentGraphRecord | None: ...
    def get_chunks(self, document_id: str, include_text: bool = False) -> list[ChunkGraphRecord]: ...
    def find_related_documents(self, document_id: str, limit: int = 10) -> list[RelatedDocumentRef]: ...
    def search_by_entity(self, query: str, limit: int) -> list[GraphCandidate]: ...
    def search_by_tag(self, query: str, limit: int) -> list[GraphCandidate]: ...
    def keyword_search(self, query: str, limit: int) -> list[GraphCandidate]: ...
    def vector_search_chunks(self, embedding: list[float], limit: int) -> list[ChunkCandidate]: ...
```

## Public API / Methods

- `Neo4jDriverProvider.get_driver`
- `Neo4jDriverProvider.resolve_database`
- `Neo4jSchemaManager.setup_schema`
- `Neo4jSchemaManager.check_schema`
- `GraphSyncService.sync_document`
- `GraphSyncService.sync_all_from_storage`
- `GraphService.get_document`
- `GraphService.get_chunks`
- `GraphService.find_related_documents`
- `GraphService.search_by_entity`
- `GraphService.search_by_tag`
- `GraphService.keyword_search`
- `GraphService.vector_search_chunks`

## Inputs

- `Neo4jConfig`.
- `ProcessedDocument` JSON loaded from storage.
- Document IDs.
- Query strings.
- Embedding vectors.
- Result limits.

## Outputs

- Neo4j driver/session access.
- Schema status.
- Graph sync results.
- Document, chunk, related-document, entity, tag, keyword, and vector search candidates.
- Manifest `neo4j_synced=true` updates after successful sync.

## Side effects

- Connects to Neo4j.
- Creates constraints, full-text indexes, and vector indexes.
- Upserts graph nodes and relationships.
- Writes chunk embeddings into Neo4j vector properties.
- Updates manifest sync state through the storage layer.

## Dependencies

- `ProcessedDocument`, `RelatedDocumentRef`, and graph DTOs from [schemas.md](schemas.md).
- `ManifestStore` and `ProcessedDocumentStore` from [core-storage-ingestion.md](core-storage-ingestion.md).
- `RetrievalService` consumes graph query methods in [retrieval-services.md](retrieval-services.md).
- `KnowledgeToolService` may call graph-facing methods through [tool-services.md](tool-services.md).

## Failure modes / risks

- Neo4j database `knowledge_base3` may be unavailable and require fallback to `neo4j`.
- Missing schema should fail clearly unless `kb ingest --auto-setup-db` is used.
- Graph sync failure should preserve processed JSON and set `neo4j_synced=false`.
- APOC-dependent behavior is out of scope for MVP.
- Graph sync must not generate embeddings or call the LLM.
- Source files must not be mutated from graph services.

## Validation

- `kb setup-db` creates required constraints and indexes without APOC.
- `Neo4jSchemaManager.check_schema` detects missing schema.
- Graph sync from JSON creates expected nodes and relationships.
- Chunk embeddings are present in Neo4j vector properties after sync.
- Retrieval can call entity, tag, keyword, and vector graph methods.
- Failed sync leaves JSON intact and manifest state accurate.

## Testing requirements

- Unit-test Cypher template construction where applicable.
- Integration-test graph sync from a sample `ProcessedDocument`.
- Integration-test schema setup/check against Neo4j.
- Integration-test search by tag/entity returning expected documents.
- Integration-test vector search returning expected chunks.

## What this must not do

- `GraphSyncService` must not parse files.
- `GraphSyncService` must not call LLMs.
- `GraphSyncService` must not generate embeddings.
- `GraphService` must not depend on CLI, LangGraph, LangChain, or future MCP adapters.
- Graph services must not mutate source files.

## Extension points

- Add graph query methods for future tool capabilities behind `GraphService`.
- Add graph DTOs in `schemas/graph.py`.
- Add future external relationship sync only after processed JSON remains rebuildable source of truth.

## Update rules

Update this file whenever Neo4j setup, graph sync behavior, graph query methods, database fallback behavior, graph failure handling, or graph service prohibitions change.
