# Schemas

## Purpose

This file defines the shared Pydantic v2 schemas and configuration classes used by the `personal_kb` MVP class design.

## When to read this

Read this when changing:

- request or response DTOs;
- document, chunk, entity, tag, relationship, manifest, or processing schemas;
- search or Q&A schemas;
- configuration classes or defaults;
- service inputs/outputs that cross package boundaries.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [core-storage-ingestion.md](core-storage-ingestion.md)
- [retrieval-services.md](retrieval-services.md)
- [qa-services.md](qa-services.md)
- [tool-services.md](tool-services.md)

## Source of truth

This file is authoritative for Pydantic schema and configuration contracts in the class design.

## Content

Schemas use Pydantic v2.

### `schemas/common.py`

#### `SourceRef`

Represents a source location inside a document.

```python
from pydantic import BaseModel

class SourceRef(BaseModel):
    file_path: str
    page: int | None = None
    section: str | None = None
    sheet: str | None = None
    cell_range: str | None = None
```

#### `ScoreBreakdown`

```python
class ScoreBreakdown(BaseModel):
    graph_score: float | None = None
    vector_score: float | None = None
    entity_score: float | None = None
    tag_score: float | None = None
    title_keyword_score: float | None = None
    reranker_score: float | None = None
    final_score: float
```

### `schemas/entity.py`

```python
from typing import Literal
from pydantic import BaseModel, Field

EntityType = Literal[
    "Person",
    "Organization",
    "Project",
    "Topic",
    "DocumentType",
    "Date",
    "MoneyAmount",
    "Account",
    "Invoice",
    "Task",
    "Technology",
    "UnknownEntity",
    "LinkedEntity",
]

class Entity(BaseModel):
    name: str
    normalized_name: str
    type: EntityType
    confidence: float | None = None
    source: str = "llm_extraction"
    summary: str | None = None
    source_chunks: list[str] = Field(default_factory=list)
```

### `schemas/tag.py`

```python
from pydantic import BaseModel

class Tag(BaseModel):
    name: str
    normalized_name: str
    confidence: float | None = None
    source: str = "llm_extraction"
```

### `schemas/chunk.py`

```python
from pydantic import BaseModel, Field
from personal_kb.schemas.common import SourceRef
from personal_kb.schemas.entity import Entity
from personal_kb.schemas.tag import Tag

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    summary: str | None = None
    tags: list[Tag] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    source_ref: SourceRef
    embedding: list[float] = Field(default_factory=list)
    embedding_model: str | None = None
```

### `schemas/document.py`

```python
from typing import Literal
from pydantic import BaseModel, Field
from personal_kb.schemas.entity import Entity
from personal_kb.schemas.tag import Tag

DocumentType = Literal["pdf", "docx", "markdown", "text", "spreadsheet"]

class Document(BaseModel):
    document_id: str
    source_id: str
    source_type: str = "local_file"
    file_path: str
    file_name: str
    file_extension: str
    document_type: DocumentType
    title: str
    summary: str | None = None
    tags: list[Tag] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    created_at: str | None = None
    modified_at: str | None = None
    ingested_at: str
    raw_bytes_hash: str
    extracted_text_hash: str | None = None
    content_hash: str
    is_duplicate: bool = False
    canonical_document_id: str | None = None
```

### `schemas/relationships.py`

```python
from typing import Literal
from pydantic import BaseModel

RelationshipType = Literal[
    "DUPLICATE_OF",
    "NEWER_VERSION_OF",
    "RELATED_TO",
]

class DocumentRelationship(BaseModel):
    type: RelationshipType
    source_document_id: str
    target_document_id: str
    confidence: float | None = None
    source: str
    reason: str | None = None
```

### `schemas/processing.py`

```python
from pydantic import BaseModel, Field

class ProcessingMetadata(BaseModel):
    parser: str
    chunker: str
    llm_model: str | None = None
    embedding_model: str | None = None
    reranker_model: str | None = None
    processed_at: str
    errors: list[str] = Field(default_factory=list)
```

### `schemas/manifest.py`

```python
from typing import Literal
from pydantic import BaseModel, Field

DocumentStatus = Literal[
    "new",
    "processed",
    "synced",
    "failed",
    "skipped",
    "duplicate",
    "versioned",
]

class ManifestDocumentEntry(BaseModel):
    document_id: str
    source_id: str
    file_path: str
    file_name: str
    file_extension: str
    raw_bytes_hash: str
    extracted_text_hash: str | None = None
    content_hash: str
    processed_json_path: str
    ingested_at: str | None = None
    modified_at: str | None = None
    neo4j_synced: bool = False
    canonical_document_id: str | None = None
    duplicate_of: str | None = None
    newer_version_of: str | None = None
    status: DocumentStatus
    error_message: str | None = None

class Manifest(BaseModel):
    schema_version: str = "0.1"
    documents: list[ManifestDocumentEntry] = Field(default_factory=list)
```

### `schemas/document.py` continued: `ProcessedDocument`

```python
from pydantic import BaseModel, Field
from personal_kb.schemas.chunk import Chunk
from personal_kb.schemas.document import Document
from personal_kb.schemas.processing import ProcessingMetadata
from personal_kb.schemas.relationships import DocumentRelationship

class ProcessedDocument(BaseModel):
    schema_version: str = "0.1"
    document: Document
    raw_text: str
    chunks: list[Chunk]
    relationships: list[DocumentRelationship] = Field(default_factory=list)
    processing: ProcessingMetadata
```

### `schemas/search.py`

```python
from typing import Literal
from pydantic import BaseModel, Field
from personal_kb.schemas.common import ScoreBreakdown, SourceRef

SearchObject = Literal["document", "entity", "tag", "chunk"]
SearchLayer = Literal["keyword", "entity", "tag", "vector", "graph"]
ScoreMode = Literal["hybrid_formula", "hybrid_formula_with_reranker", "reranker_only"]

class SearchPlan(BaseModel):
    search_objects: list[SearchObject] = Field(
        default_factory=lambda: ["document", "entity", "tag", "chunk"]
    )
    priority: list[SearchLayer] = Field(
        default_factory=lambda: ["keyword", "entity", "vector", "graph"]
    )
    top_k: int = 10
    reranker: str = "local_cross_encoder"
    score_mode: ScoreMode = "hybrid_formula_with_reranker"
    include_related_documents: bool = True
    include_chunks: bool = True

class SearchDocumentsRequest(BaseModel):
    query: str
    search_plan: SearchPlan = Field(default_factory=SearchPlan)

class MatchedChunk(BaseModel):
    chunk_id: str
    source_ref: SourceRef
    summary: str | None = None
    text: str | None = None
    score: float | None = None
    reason: str | None = None

class RelatedDocumentRef(BaseModel):
    document_id: str
    relationship: str
    confidence: float | None = None
    reason: str | None = None

class SearchDocumentResult(BaseModel):
    document_id: str
    title: str
    file_path: str
    document_type: str
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None
    modified_at: str | None = None
    confidence: float
    score_breakdown: ScoreBreakdown
    matched_entities: list[str] = Field(default_factory=list)
    matched_chunks: list[MatchedChunk] = Field(default_factory=list)
    related_documents: list[RelatedDocumentRef] = Field(default_factory=list)

class SearchDocumentsResponse(BaseModel):
    query: str
    search_mode: list[str]
    results: list[SearchDocumentResult]
    warnings: list[str] = Field(default_factory=list)
```

### `schemas/qa.py`

```python
from pydantic import BaseModel, Field
from personal_kb.schemas.search import SearchPlan, MatchedChunk
from personal_kb.schemas.common import SourceRef

class AnswerQuestionRequest(BaseModel):
    question: str
    search_plan: SearchPlan = Field(default_factory=SearchPlan)
    include_supporting_chunk_text: bool = True
    top_k_chunks: int = 8

class SourceDocumentRef(BaseModel):
    document_id: str
    title: str
    file_path: str
    source_refs: list[SourceRef] = Field(default_factory=list)

class AnswerQuestionResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    source_documents: list[SourceDocumentRef]
    supporting_chunks: list[MatchedChunk]
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

### `schemas/config.py`

```python
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    package_name: str = "personal_kb"
    documents_dir: str = "data"
    storage_dir: str = "kb_storage"
    benchmark_dir: str = "benchmark"
    path_mode: str = "relative"

class Neo4jConfig(BaseModel):
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password_env: str = "NEO4J_PASSWORD"
    database: str = "knowledge_base3"
    fallback_database: str = "neo4j"
    apoc_required: bool = False
    schema_setup_mode: str = "explicit_kb_setup_db"
    ingest_auto_sync: bool = True

class LLMConfig(BaseModel):
    provider: str = "lmstudio_openai_compatible"
    base_url: str = "http://localhost:1234/v1"
    model_name: str = "mlx-community/Qwen3.5-9B-OptiQ-4bit"
    runtime: str = "mlx-lm"
    quantization: str = "mixed_precision_4bit"
    role: str = "production_default"

class EmbeddingConfig(BaseModel):
    provider: str = "local"
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    dimension: int = 1024
    context_length: int = 32768
    normalize_embeddings: bool = True
    instruction_aware: bool = True
    execution: str = "transformers_or_sentence_transformers"
    store_full_vectors_in_json: bool = True

class RerankerConfig(BaseModel):
    provider: str = "local"
    model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    context_length: int = 32768
    top_k_before_rerank: int = 50
    top_k_after_rerank: int = 8
    instruction_aware: bool = True
    execution: str = "transformers_or_sentence_transformers"

class ParserConfig(BaseModel):
    pdf_primary: str = "pdfplumber"
    pdf_fallback: str = "pymupdf"
    pdf_ocr: bool = False
    docx_primary: str = "mammoth"
    docx_fallback: str = "python-docx"
    xlsx_primary: str = "openpyxl"

class SearchConfig(BaseModel):
    default_top_k: int = 10
    include_related_documents: bool = True
    include_chunks: bool = True
    score_mode: str = "hybrid_formula_with_reranker"
    weights: dict[str, float] = Field(default_factory=lambda: {
        "graph_score": 0.25,
        "vector_score": 0.20,
        "entity_score": 0.15,
        "tag_score": 0.10,
        "title_keyword_score": 0.10,
        "reranker_score": 0.20,
    })

class PersonalKBConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    parsers: ParserConfig = Field(default_factory=ParserConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
```

## Public API / Methods

The public API is the set of Pydantic models, literals, and config classes listed above. Services should exchange these schemas rather than unstructured dictionaries across package boundaries.

## Inputs

Schema instances are populated from local files, parser output, config files, Neo4j query results, search requests, Q&A requests, and adapter inputs from CLI, LangChain tools, or future MCP.

## Outputs

Outputs are validated Pydantic objects that can be serialized to JSON for storage, CLI rendering, LangChain StructuredTool outputs, future MCP responses, benchmarks, and tests.

## Side effects

Schemas should have no filesystem, Neo4j, model-runtime, or network side effects.

## Dependencies

- Pydantic v2.
- `SourceRef` and `ScoreBreakdown` from `schemas/common.py`.
- Search and Q&A schemas used by [retrieval-services.md](retrieval-services.md), [qa-services.md](qa-services.md), and [tool-services.md](tool-services.md).
- Manifest and document schemas used by [core-storage-ingestion.md](core-storage-ingestion.md) and [graph-services.md](graph-services.md).

## Failure modes / risks

- Schema field drift can break stored JSON compatibility.
- Changing defaults in `SearchPlan` or config classes changes retrieval behavior.
- Changing embedding dimensions can invalidate existing vectors in JSON and Neo4j.
- Removing warnings, missing-information fields, or score details weakens validation and grounding.

## Validation

- Pydantic validation should reject invalid stored JSON and invalid adapter inputs.
- Round-trip `ProcessedDocument` through JSON storage.
- Validate `Manifest` load/save behavior with `ManifestDocumentEntry.status` values.
- Verify search and Q&A responses include warnings lists even when empty.

## Testing requirements

- Unit-test schema defaults and required fields.
- Unit-test config defaults and env-dependent validation through `ConfigLoader`.
- Add compatibility tests before changing stored JSON schema shape.

## What this must not do

- Do not perform parsing, chunking, embedding, graph sync, retrieval, answer generation, CLI rendering, or external calls in schema classes.
- Do not use schemas to hide service logic in validators.

## Extension points

- Add future tool schemas to `schemas/tools.py`.
- Add future graph DTOs to `schemas/graph.py`.
- Add new document types by extending `DocumentType` and the parser/chunker registries together.

## Update rules

Update this file whenever schema modules, fields, defaults, literals, config classes, request models, response models, or storage contract assumptions change.
