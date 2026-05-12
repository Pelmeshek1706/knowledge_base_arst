# Core, Storage, and Ingestion Services

## Purpose

This file defines the deterministic local processing pipeline for `personal_kb`: core utilities, storage stores, parser and chunker registries, file discovery, duplicate/version planning, and ingestion orchestration.

## When to read this

Read this when changing:

- config loading, path handling, hashing, or normalization;
- manifest or processed JSON persistence;
- parser or chunker contracts;
- local file discovery;
- duplicate/version decision behavior;
- ingestion flow or failed-document handling.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [model-extraction-services.md](model-extraction-services.md)
- [graph-services.md](graph-services.md)

## Source of truth

This file is authoritative for core utility classes, storage classes, parser/chunker contracts, and deterministic ingestion class design.

## Content

### Core utilities

#### `ConfigLoader`

**File:** `core/config_loader.py`

Responsibility:

- Load `configs/config.yaml`.
- Validate into `PersonalKBConfig`.
- Resolve environment variables.
- Provide config to composition root.

```python
class ConfigLoader:
    def load(self, path: str = "configs/config.yaml") -> PersonalKBConfig:
        ...
```

Failure modes:

- Config file missing.
- Invalid YAML.
- Invalid Pydantic schema.
- Missing required environment variables.

#### `PathResolver`

**File:** `core/paths.py`

Responsibility:

- Resolve project-relative paths.
- Convert absolute file paths to relative paths for JSON storage.
- Prevent path traversal outside project root.

```python
class PathResolver:
    def __init__(self, project_root: Path, path_mode: str = "relative") -> None: ...
    def to_storage_path(self, path: Path) -> str: ...
    def resolve_documents_dir(self) -> Path: ...
    def resolve_storage_dir(self) -> Path: ...
```

#### `HashingService`

**File:** `core/hashing.py`

Responsibility:

- Compute `raw_bytes_hash` before parsing.
- Compute `extracted_text_hash` after parsing.
- Derive `content_hash` from both when needed.

```python
class HashingService:
    def hash_file_bytes(self, path: Path) -> str: ...
    def hash_text(self, text: str) -> str: ...
    def make_content_hash(self, raw_bytes_hash: str, extracted_text_hash: str | None) -> str: ...
```

MVP rule:

```text
raw_bytes_hash is always available.
extracted_text_hash is available after parsing.
content_hash should prefer raw_bytes_hash for exact duplicate detection.
```

#### `NormalizationService`

**File:** `core/normalization.py`

Responsibility:

- Normalize tags/entities.
- Lowercase, trim, collapse spaces.
- Future: LLM canonicalization.

```python
class NormalizationService:
    def normalize_label(self, value: str) -> str: ...
    def normalize_entity_name(self, value: str) -> str: ...
    def normalize_tag_name(self, value: str) -> str: ...
```

### Storage layer

#### `ManifestStore`

**File:** `storage/manifest_store.py`

Responsibility:

- Load/save `kb_storage/manifest.json`.
- Query entries by path/hash/document_id.
- Persist failed documents with `status="failed"` and `error_message`.
- Update `neo4j_synced` state.

```python
class ManifestStore:
    def load(self) -> Manifest: ...
    def save(self, manifest: Manifest) -> None: ...
    def get_by_source_id(self, source_id: str) -> ManifestDocumentEntry | None: ...
    def get_by_raw_bytes_hash(self, raw_bytes_hash: str) -> list[ManifestDocumentEntry]: ...
    def add_or_update(self, entry: ManifestDocumentEntry) -> None: ...
    def mark_synced(self, document_id: str) -> None: ...
    def mark_failed(self, source_id: str, error_message: str) -> None: ...
```

Implementation notes:

- Writes should be atomic: write temp file, then replace.
- Keep manifest human-readable with indentation.
- Do not store full raw text in manifest.

#### `ProcessedDocumentStore`

**File:** `storage/processed_document_store.py`

Responsibility:

- Read/write `kb_storage/documents/<document_id>.json`.
- Validate `ProcessedDocument` schema on load.
- Keep embeddings as full arrays in JSON.

```python
class ProcessedDocumentStore:
    def save(self, processed_document: ProcessedDocument) -> Path: ...
    def load(self, document_id: str) -> ProcessedDocument: ...
    def exists(self, document_id: str) -> bool: ...
    def iter_documents(self) -> Iterator[ProcessedDocument]: ...
```

### Parser layer

#### `BaseParser`

**File:** `parsers/base.py`

```python
from typing import Protocol

class BaseParser(Protocol):
    supported_extensions: set[str]

    def parse(self, path: Path) -> ParsedDocument:
        ...
```

`ParsedDocument` should include:

```python
class ParsedDocument(BaseModel):
    source_id: str
    source_type: str = "local_file"
    file_path: str
    file_name: str
    file_extension: str
    title: str
    raw_text: str
    structured_blocks: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
```

#### Parser implementations

| Class | File | Primary library | Fallback | Responsibility |
|---|---|---|---|---|
| `PdfParser` | `pdf_parser.py` | `pdfplumber` | `PyMuPDF` | page-aware text extraction |
| `DocxParser` | `docx_parser.py` | `mammoth` | `python-docx` | heading/paragraph/table extraction |
| `MarkdownParser` | `markdown_parser.py` | built-in | none | preserve heading hierarchy |
| `TxtParser` | `txt_parser.py` | built-in | none | plain text extraction |
| `XlsxParser` | `xlsx_parser.py` | `openpyxl` | none | workbook/sheet/range extraction |

#### `ParserRegistry`

```python
class ParserRegistry:
    def __init__(self, parsers: list[BaseParser]) -> None: ...
    def get_parser(self, file_extension: str) -> BaseParser: ...
    def is_supported(self, file_extension: str) -> bool: ...
```

### Chunking layer

#### `BaseChunker`

```python
class BaseChunker(Protocol):
    def chunk(self, parsed_document: ParsedDocument, document_id: str) -> list[Chunk]:
        ...
```

#### Chunker implementations

| Class | Strategy |
|---|---|
| `PdfChunker` | page-aware chunks |
| `DocxChunker` | heading-aware chunks |
| `MarkdownChunker` | heading-aware chunks |
| `TxtChunker` | fixed-size chunks |
| `XlsxChunker` | sheet/table/range chunks |

#### `ChunkerRegistry`

```python
class ChunkerRegistry:
    def get_chunker(self, document_type: str) -> BaseChunker: ...
```

### Ingestion layer

#### `FileDiscoveryService`

**File:** `ingestion/file_discovery.py`

Responsibility:

- Scan `data/`.
- Filter supported extensions.
- Return file candidates.

```python
class FileDiscoveryService:
    def discover(self, documents_dir: Path) -> list[Path]: ...
```

#### `ProcessingPlanner`

**File:** `ingestion/processing_planner.py`

Responsibility:

- Decide what to do before expensive processing.
- Use manifest + raw bytes hash.

```python
class ProcessingAction(str, Enum):
    SKIP = "skip"
    PROCESS_NEW = "process_new"
    CREATE_VERSION = "create_version"
    CREATE_DUPLICATE = "create_duplicate"

class ProcessingPlanner:
    def plan(self, file_path: Path, raw_bytes_hash: str, manifest: Manifest) -> ProcessingDecision:
        ...
```

Rules:

| Case | Action |
|---|---|
| same path + same raw hash | `SKIP` |
| same path + different raw hash | `CREATE_VERSION` |
| different path + same raw hash | `CREATE_DUPLICATE` |
| no match | `PROCESS_NEW` |

Changed file behavior is automatic `NEWER_VERSION_OF`, not interactive.

#### `DuplicateDetector`

**File:** `ingestion/duplicate_detector.py`

Responsibility:

- Detect exact duplicates by raw bytes hash and optionally extracted text hash.
- Choose canonical by `modified_at`, fallback `ingested_at`.

```python
class DuplicateDetector:
    def find_exact_duplicates(self, raw_bytes_hash: str, manifest: Manifest) -> list[ManifestDocumentEntry]: ...
    def choose_canonical(self, entries: list[ManifestDocumentEntry]) -> str: ...
```

#### `IngestionService`

**File:** `ingestion/ingestion_service.py`

Responsibility:

- Orchestrate deterministic ingestion.
- No agent involvement.
- Optionally sync Neo4j after each processed document.

```python
class IngestionService:
    def ingest_path(self, path: Path) -> IngestionRunResult: ...
    def ingest_file(self, path: Path) -> DocumentProcessingResult: ...
```

Dependencies:

```text
FileDiscoveryService
HashingService
ManifestStore
ParserRegistry
ChunkerRegistry
StructuredExtractor
EmbeddingClient
ProcessedDocumentStore
GraphSyncService
```

High-level flow:

```text
scan files
-> raw hash
-> processing decision
-> parse
-> extracted text hash
-> chunk
-> extract summaries/tags/entities
-> embed chunks
-> save processed JSON
-> sync Neo4j
-> update manifest
```

Failure handling:

- Failed documents stay in manifest.
- `status="failed"`.
- Store `error_message`.

## Public API / Methods

The public methods are the class methods listed above, especially:

- `ConfigLoader.load`
- `PathResolver.to_storage_path`
- `PathResolver.resolve_documents_dir`
- `PathResolver.resolve_storage_dir`
- `HashingService.hash_file_bytes`
- `HashingService.hash_text`
- `HashingService.make_content_hash`
- `NormalizationService.normalize_label`
- `ManifestStore.load`
- `ManifestStore.save`
- `ManifestStore.add_or_update`
- `ManifestStore.mark_synced`
- `ManifestStore.mark_failed`
- `ProcessedDocumentStore.save`
- `ProcessedDocumentStore.load`
- `ProcessedDocumentStore.iter_documents`
- `ParserRegistry.get_parser`
- `ChunkerRegistry.get_chunker`
- `ProcessingPlanner.plan`
- `DuplicateDetector.find_exact_duplicates`
- `DuplicateDetector.choose_canonical`
- `IngestionService.ingest_path`
- `IngestionService.ingest_file`

## Inputs

- Local file paths under `data/`.
- `configs/config.yaml`.
- `kb_storage/manifest.json`.
- Existing `kb_storage/documents/<document_id>.json`.
- Parser and chunker registry configuration.
- `Manifest`, `ProcessedDocument`, `Chunk`, `Document`, and related schemas from [schemas.md](schemas.md).

## Outputs

- Validated `PersonalKBConfig`.
- Stable hashes.
- Normalized labels and names.
- Manifest entries.
- `ProcessedDocument` JSON.
- Ingestion run and document processing results.
- Failed-document records with `status="failed"` and `error_message`.

## Side effects

- Reads local source files.
- Writes `kb_storage/manifest.json`.
- Writes `kb_storage/documents/<document_id>.json`.
- May call `GraphSyncService` after processing when auto-sync is enabled.
- Must not mutate source files.

## Dependencies

- [schemas.md](schemas.md) for config, manifest, document, chunk, and processing models.
- [model-extraction-services.md](model-extraction-services.md) for `StructuredExtractor` and `EmbeddingClient`.
- [graph-services.md](graph-services.md) for optional `GraphSyncService`.

## Failure modes / risks

- Missing or invalid config blocks ingestion startup.
- Path traversal must be rejected by `PathResolver`.
- Non-atomic manifest writes can corrupt processed state.
- Parser or chunker failures must not silently skip files.
- Duplicate/version decisions must happen before expensive parsing/model calls.
- Failed documents must stay visible in manifest, not disappear from state.
- Auto-sync failures must preserve processed JSON and manifest status accurately.

## Validation

- `ConfigLoader` validates good and bad YAML plus env resolution.
- `HashingService` returns stable hashes and detects changed content.
- `ManifestStore` load/save/update/failed-state behavior round-trips.
- `ProcessedDocumentStore` validates schema on load.
- Parser smoke tests cover supported file types.
- Chunker tests verify `source_ref` correctness.
- `ProcessingPlanner` tests cover skip/version/duplicate/new cases.
- Ingestion integration tests create JSON + manifest for TXT/MD documents.

## Testing requirements

- Unit-test deterministic functions without model or Neo4j dependencies.
- Use fixture files for parser/chunker smoke tests.
- Integration-test failed-document handling.
- Integration-test duplicate and changed-file behavior:
  - duplicate file -> separate `Document` + `DUPLICATE_OF`;
  - changed file -> new `Document` + `NEWER_VERSION_OF`.

## What this must not do

- `Parser` classes must not write to Neo4j.
- `BaseChunker` must not extract entities.
- `HashingService` must not parse files.
- `ManifestStore` must not parse or sync graph data.
- `ProcessedDocumentStore` must not mutate Neo4j.
- `ProcessingPlanner` must not process file content.
- `IngestionService` must not answer user questions.
- Ingestion must not be agent-controlled in MVP.

## Extension points

- Add parser/chunker implementations for new file formats through registries.
- Add future LLM canonicalization behind `NormalizationService`.
- Add optional extracted-text duplicate detection after the raw hash decision remains intact.
- Add alternate storage implementations only behind the same schema contracts.

## Update rules

Update this file whenever utility behavior, storage persistence, parser/chunker contracts, ingestion flow, duplicate/version rules, failure handling, or deterministic processing ownership changes.
