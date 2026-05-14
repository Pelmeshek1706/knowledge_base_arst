# Model and Extraction Services

## Purpose

This file defines local model client classes and extraction services used by `personal_kb` for summaries, structured metadata, embeddings, reranking, and document-level aggregation.

## When to read this

Read this when changing:

- LM Studio LLM client behavior;
- embedding or reranker model configuration;
- structured extraction JSON validation;
- chunk summary/tag/entity extraction;
- document-level metadata aggregation;
- retry behavior for invalid model output.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [core-storage-ingestion.md](core-storage-ingestion.md)
- [retrieval-services.md](retrieval-services.md)
- [qa-services.md](qa-services.md)

## Source of truth

This file is authoritative for local model client and extraction/aggregation class design.

## Content

### Local model layer

#### `LLMClient`

**File:** `models/llm_client.py`

Responsibility:

- Call LM Studio OpenAI-compatible endpoint.
- Generate summaries.
- Generate structured extraction JSON.
- Generate final answers.
- For compatible reasoning models, optionally accept structured JSON from
  `reasoning_content` only when visible assistant content is empty and the
  reasoning payload validates against the requested schema.

```python
class LLMClient:
    def generate_text(self, prompt: str, *, temperature: float = 0.0) -> str: ...
    def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
```

MVP model:

```text
mlx-community/Qwen3.5-9B-OptiQ-4bit
```

Dedicated extraction model config:

```text
qwen2.5-1.5b-instruct
```

#### `EmbeddingClient`

**File:** `models/embedding_client.py`

Responsibility:

- Run `Qwen/Qwen3-Embedding-0.6B` locally via `transformers` / `sentence-transformers`.
- Return normalized 1024-dimensional embeddings.

```python
class EmbeddingClient:
    dimension: int = 1024

    def embed_text(self, text: str, *, instruction: str | None = None) -> list[float]: ...
    def embed_batch(self, texts: list[str], *, instruction: str | None = None) -> list[list[float]]: ...
```

#### `RerankerClient`

**File:** `models/reranker_client.py`

Responsibility:

- Run `Qwen/Qwen3-Reranker-0.6B` locally.
- Score query-document/chunk pairs.
- Select top-k after reranking.

```python
class RerankerClient:
    def score_pairs(self, query: str, texts: list[str]) -> list[float]: ...
    def rerank(self, query: str, candidates: list[SearchDocumentResult], top_k: int) -> list[SearchDocumentResult]: ...
```

### Extraction layer

#### `StructuredExtractor`

**File:** `extraction/structured_extractor.py`

Responsibility:

- Generate chunk summaries.
- Generate chunk tags.
- Preserve chunk entities as an empty validated list until typed entity
  extraction has separate model evidence.
- Aggregate document-level summary/tags/entities.
- Validate model output with Pydantic.
- Retry on invalid JSON.

```python
class StructuredExtractor:
    def extract_chunk_metadata(self, chunk: Chunk) -> ChunkExtractionResult: ...
    def aggregate_document_metadata(self, chunks: list[Chunk]) -> DocumentExtractionResult: ...
```

#### `DocumentMetadataAggregator`

**File:** `extraction/aggregation.py`

Responsibility:

- Merge tags and entities across chunks.
- Normalize duplicate entity/tag names.
- Produce document-level entity summaries.

```python
class DocumentMetadataAggregator:
    def aggregate_tags(self, chunks: list[Chunk]) -> list[Tag]: ...
    def aggregate_entities(self, chunks: list[Chunk]) -> list[Entity]: ...
```

## Public API / Methods

- `LLMClient.generate_text`
- `LLMClient.generate_json`
- `EmbeddingClient.embed_text`
- `EmbeddingClient.embed_batch`
- `RerankerClient.score_pairs`
- `RerankerClient.rerank`
- `StructuredExtractor.extract_chunk_metadata`
- `StructuredExtractor.aggregate_document_metadata`
- `DocumentMetadataAggregator.aggregate_tags`
- `DocumentMetadataAggregator.aggregate_entities`

## Inputs

- Prompt strings.
- Pydantic schema classes for JSON validation.
- Chunk text and `Chunk` schemas.
- Candidate `SearchDocumentResult` objects.
- Local model config from `PersonalKBConfig`.

## Outputs

- Generated text.
- Validated Pydantic objects from structured JSON.
- Normalized 1024-dimensional embeddings.
- Reranked search candidates.
- Chunk-level summaries/tags/entities.
- Document-level summaries/tags/entities.

## Side effects

- Calls local LM Studio OpenAI-compatible endpoint.
- Runs local embedding and reranker models through `transformers` / `sentence-transformers`.
- Does not write files or mutate Neo4j directly.

## Dependencies

- `LLMConfig`, `EmbeddingConfig`, and `RerankerConfig` from [schemas.md](schemas.md).
- `Chunk`, `Tag`, `Entity`, and search schemas from [schemas.md](schemas.md).
- `NormalizationService` from [core-storage-ingestion.md](core-storage-ingestion.md).
- `RetrievalService` uses `EmbeddingClient` and `RerankerClient` in [retrieval-services.md](retrieval-services.md).
- `AnswerGenerator` uses `LLMClient` in [qa-services.md](qa-services.md).

## Failure modes / risks

- LM Studio endpoint unavailable.
- Model returns invalid JSON.
- Reasoning models can return schema-valid JSON in `reasoning_content` with
  empty visible content; this compatibility path must remain explicit,
  schema-validated, and visible in response metadata/warnings.
- Embedding model returns wrong dimension or non-normalized vectors.
- Reranker scores are unavailable or incompatible with candidate order.
- Extraction output may duplicate tags/entities unless normalized.
- Embedding failures may be recoverable by marking chunks as missing embedding.

## Validation

- Validate `generate_json` output against the provided Pydantic schema.
- Retry invalid structured extraction output, then fail clearly if still invalid.
- Assert embedding vectors are 1024-dimensional and normalized when configured.
- Unit-test metadata aggregation duplicate merging.
- Retrieval tests should prove reranker integration does not remove required source metadata.

## Testing requirements

- Unit-test prompt-to-schema validation with mocked LLM responses.
- Unit-test embedding dimensions and batch ordering with mocked model output.
- Unit-test reranker ordering and top-k behavior.
- Integration-test extraction on small TXT/MD chunks once local model runtime is available.

## What this must not do

- `LLMClient` must not persist documents or query Neo4j.
- `EmbeddingClient` must not decide retrieval ranking beyond vector generation.
- `RerankerClient` must not retrieve candidates.
- `StructuredExtractor` must not write graph data.
- Extraction must not create required document relationships as part of MVP.

## Extension points

- Add alternate local model providers behind the same client methods.
- Add prompt variants in `extraction/prompts.py`.
- Add future LLM canonicalization through `NormalizationService`.
- Add richer extraction result schemas without breaking stored document contracts.

## Update rules

Update this file whenever local model choices, model client methods, extraction schemas, retry behavior, metadata aggregation, or model-related validation rules change.
