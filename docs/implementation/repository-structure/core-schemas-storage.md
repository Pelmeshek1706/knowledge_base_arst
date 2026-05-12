# Core, Schemas, And Storage

## Purpose

This file defines the foundation modules for shared utilities, Pydantic contracts, manifest storage, and processed document JSON storage.

## When to read this

Read this when implementing or changing `personal_kb/core/`, `personal_kb/schemas/`, or `personal_kb/storage/`.

## Related files

- [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md)
- [ingestion-parsing-models.md](ingestion-parsing-models.md)
- [graph-retrieval-qa.md](graph-retrieval-qa.md)
- [../class-design/schemas.md](../class-design/schemas.md)
- [../class-design/core-storage-ingestion.md](../class-design/core-storage-ingestion.md)

## Source of truth

This file is authoritative for repository structure and responsibilities of core utilities, shared schemas, and storage modules. Detailed class behavior is owned by the class-design documents.

## Content

## `personal_kb/core/`

Purpose:

- shared infrastructure utilities;
- no business workflow;
- no Neo4j queries;
- no LLM calls.

### `config.py`

Defines internal config dataclasses/Pydantic models if not placed in `schemas/config.py`.

Used by:

- `config_loader.py`;
- service factories;
- CLI startup;
- tests.

### `config_loader.py`

Responsibilities:

- load YAML config from `configs/default.yaml`;
- apply environment variable overrides;
- validate final config;
- expose one typed `AppConfig` object.

Must not:

- connect to Neo4j;
- initialize models;
- perform ingestion.

### `hashing.py`

Responsibilities:

- compute raw bytes hash;
- compute extracted text hash;
- use SHA256;
- expose deterministic hashing helpers.

Used by:

- `ingestion_planner.py`;
- `duplicate_service.py`;
- `versioning_service.py`;
- tests.

Key functions:

```python
compute_file_sha256(path: Path) -> str
compute_text_sha256(text: str) -> str
```

### `normalization.py`

Responsibilities:

- normalize tags/entities using MVP rule:

```text
lowercase + trim + collapse spaces
```

Used by:

- extraction aggregation;
- graph sync;
- retrieval;
- duplicate/relationship building.

### `paths.py`

Responsibilities:

- convert absolute paths to configured relative paths;
- resolve project root;
- resolve `data/`, `kb_storage/`, `benchmark/`.

### `exceptions.py`

Defines project-specific exceptions:

```text
PersonalKBError
ConfigError
ManifestError
ParsingError
ExtractionError
EmbeddingError
GraphSyncError
RetrievalError
QAError
ToolExecutionError
```

## `personal_kb/schemas/`

Purpose:

- Pydantic contracts shared across all layers;
- source of truth for data shape;
- used by services, storage, tools, CLI, LangGraph, and future MCP adapter.

### `document.py`

Defines:

```python
DocumentRecord
DocumentMetadata
DocumentType
SourceReference
```

Used by:

- parser outputs;
- processed document JSON;
- graph sync;
- search results.

### `chunk.py`

Defines:

```python
ChunkRecord
ChunkSourceRef
ChunkEmbedding
```

Used by:

- chunkers;
- extraction service;
- embedding service;
- Neo4j vector index;
- Q&A context builder.

### `entity.py`

Defines:

```python
EntityRecord
EntityType
EntityMention
```

MVP entity types:

```text
Person
Organization
Project
Topic
DocumentType
Date
MoneyAmount
Account
Invoice
Task
Technology
UnknownEntity
LinkedEntity
```

### `tag.py`

Defines:

```python
TagRecord
```

Fields should include:

```text
name
normalized_name
confidence
source
source_chunks
```

### `manifest.py`

Defines:

```python
Manifest
ManifestDocumentEntry
ProcessingStatus
```

Statuses:

```text
new
processed
synced
skipped
duplicate
failed
```

Failed documents must stay in manifest with error message.

### `processing.py`

Defines:

```python
RawDocument
ParsedDocument
ProcessedDocument
ProcessingMetadata
ProcessingError
```

Used by:

- parsers;
- ingestion service;
- processed document store;
- graph sync.

### `search.py`

Defines:

```python
SearchPlan
SearchDocumentsRequest
SearchDocumentsResponse
SearchResultItem
ScoreBreakdown
MatchedChunk
RelatedDocument
```

`SearchPlan` describes **how** to search, not **what** to search.

Example responsibilities:

- which search layers to use;
- layer priority;
- top-k values;
- reranker usage;
- score mode;
- whether to include chunks and related documents.

### `qa.py`

Defines:

```python
AnswerQuestionRequest
AnswerQuestionResponse
SourceDocumentReference
SupportingChunk
WarningMessage
MissingInformation
```

### `tools.py`

Defines tool-facing request/response aliases and schemas.

Used by:

- `tools/knowledge_tool_service.py`;
- `tools/structured_tools.py`;
- future MCP adapter.

### `errors.py`

Defines structured error response schemas:

```python
ErrorResponse
ToolErrorResponse
ValidationErrorDetail
```

## `personal_kb/storage/`

Purpose:

- read/write manifest and processed JSON;
- no parsing;
- no LLM calls;
- no Neo4j queries except sync status metadata if explicitly required.

### `manifest_store.py`

Responsibilities:

- create/load/save `kb_storage/manifest.json`;
- update document status;
- find by source path;
- find by raw bytes hash;
- find by extracted text hash;
- record failures;
- record Neo4j sync status.

Key methods:

```python
load_manifest() -> Manifest
save_manifest(manifest: Manifest) -> None
get_entry_by_source_id(source_id: str) -> ManifestDocumentEntry | None
find_by_raw_bytes_hash(hash_value: str) -> list[ManifestDocumentEntry]
find_by_extracted_text_hash(hash_value: str) -> list[ManifestDocumentEntry]
mark_failed(document_id: str, error: str) -> None
mark_synced(document_id: str) -> None
```

Used by:

- ingestion planner;
- graph sync service;
- CLI status command;
- evaluation diagnostics.

### `processed_document_store.py`

Responsibilities:

- save per-document JSON;
- load per-document JSON;
- validate schema version;
- list processed documents.

Key methods:

```python
save(document: ProcessedDocument) -> Path
load(document_id: str) -> ProcessedDocument
exists(document_id: str) -> bool
list_documents() -> list[ProcessedDocument]
```

Used by:

- ingestion service;
- graph sync service;
- document service;
- Q&A context builder if full text is needed.

## Dependencies

- `configs/default.yaml`
- `.env.example`
- `kb_storage/manifest.json`
- `kb_storage/documents/<document_id>.json`
- `personal_kb/schemas/*`

## Failure modes / risks

- Config loading can accidentally initialize services or perform I/O beyond config validation.
- Manifest failures can disappear if failed documents are removed instead of retained with an error message.
- Storage can become non-deterministic if it mutates parsed content or calls model/graph layers.
- Schema changes can break stored processed JSON if schema version validation is not maintained.

## Validation

- Unit test hashing, normalization, manifest store behavior, and processed document store behavior.
- Confirm failed documents remain in the manifest with an error message.
- Confirm `ProcessedDocument` JSON can be loaded and validated by the current schema version.
- Confirm storage modules do not import parser, LLM, Neo4j query, CLI, LangGraph, or tool wrapper logic.

## Update rules

Update this file when core helpers, shared schemas, manifest fields/statuses, storage methods, processed JSON shape, or storage responsibility boundaries change.
