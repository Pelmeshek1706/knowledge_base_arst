# Model Strategy

## Purpose

This file defines the local model architecture for LLM calls, embeddings, reranking, structured extraction, normalization, and document type classification.

## When to read this

Read this file when changing local model providers, model names, embedding dimensions, reranker behavior, extraction prompts, extraction schemas, tag/entity normalization, document type rules, model abstractions, or model-related validation.

## Related files

- [overview.md](overview.md)
- [storage-design.md](storage-design.md)
- [graph-schema.md](graph-schema.md)
- [retrieval-design.md](retrieval-design.md)
- [qa-design.md](qa-design.md)

## Source of truth

This file is authoritative for local LLM configuration, embedding configuration, reranker configuration, model abstraction boundaries, chunk-level extraction, document-level aggregation, entity/tag structures, normalization rules, entity types, and document type mapping.

## Content

### Responsibility

The local model layer is responsible for:

- summaries
- tag extraction
- entity extraction
- embeddings
- reranking
- answer generation

Provider boundaries should be explicit even though MVP uses only local models. The goal is to prevent model calls from leaking into business logic.

### Component boundaries

Model clients should not:

- decide ingestion state transitions;
- write processed JSON directly;
- mutate Neo4j directly;
- own retrieval scoring policy;
- own LangGraph routing;
- bypass schema validation.

Business services should call explicit model-client abstractions instead of embedding model calls inside parsers, graph sync, tools, or CLI wrappers.

### Active MVP provider strategy

```text
local only
```

### LLM

```yaml
llm:
  provider: lmstudio_openai_compatible
  base_url: http://localhost:1234/v1
  model_name: mlx-community/Qwen3.5-9B-OptiQ-4bit
  runtime: mlx-lm
  quantization: mixed_precision_4bit
  role: production_default
```

### Embedding model

```yaml
embedding:
  provider: local_transformers_or_sentence_transformers
  model_name: Qwen/Qwen3-Embedding-0.6B
  dimension: 1024
  context_length: 32768
  normalize_embeddings: true
  instruction_aware: true
  store_full_vectors_in_json: true
```

### Reranker model

```yaml
reranker:
  provider: local_transformers_or_sentence_transformers
  model_name: Qwen/Qwen3-Reranker-0.6B
  context_length: 32768
  top_k_before_rerank: 50
  top_k_after_rerank: 8
  instruction_aware: true
```

### Suggested abstractions

```text
LLMClient
EmbeddingClient
RerankerClient
StructuredExtractionClient
```

### Extraction strategy

Extraction is done per chunk, then aggregated to document level.

For each chunk:

- summary
- tags
- entities

Entity structure:

```json
{
  "name": "Penelope",
  "normalized_name": "penelope",
  "type": "Person",
  "confidence": 0.91,
  "source": "llm_extraction"
}
```

Tag structure:

```json
{
  "name": "Project Budget",
  "normalized_name": "project budget",
  "confidence": 0.88,
  "source": "llm_extraction"
}
```

### Normalization

MVP normalization:

```text
lowercase
trim
collapse repeated spaces
```

LLM-based canonicalization is future-only.

### Document-level aggregation

Document-level fields are derived from chunks:

- global summary
- global tags
- global entities
- entity summaries

Example:

```json
{
  "entities": [
    {
      "name": "Penelope",
      "normalized_name": "penelope",
      "type": "Person",
      "confidence": 0.91,
      "summary": "Mentioned as a recipient/contact related to accounting documents.",
      "source_chunks": ["chunk_1", "chunk_7"]
    }
  ]
}
```

### Entity types

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

### Document type

`document_type` is one value based on file extension:

| Extension | document_type |
|---|---|
| `.pdf` | `pdf` |
| `.docx` | `docx` |
| `.md` | `markdown` |
| `.txt` | `text` |
| `.xlsx` | `spreadsheet` |

Semantic types such as `invoice`, `budget`, `report`, `article`, `meeting_notes` should be tags, not document type.

### Model-related configuration

The model portions of the file-based configuration are:

```yaml
models:
  llm:
    provider: lmstudio_openai_compatible
    base_url: http://localhost:1234/v1
    model_name: mlx-community/Qwen3.5-9B-OptiQ-4bit
    runtime: mlx-lm
    quantization: mixed_precision_4bit
    role: production_default

  embedding:
    provider: local_transformers_or_sentence_transformers
    model_name: Qwen/Qwen3-Embedding-0.6B
    dimension: 1024
    context_length: 32768
    normalize_embeddings: true
    instruction_aware: true
    store_full_vectors_in_json: true

  reranker:
    provider: local_transformers_or_sentence_transformers
    model_name: Qwen/Qwen3-Reranker-0.6B
    context_length: 32768
    top_k_before_rerank: 50
    top_k_after_rerank: 8
    instruction_aware: true

normalization:
  tag_entity_normalization: lowercase_trim_collapse_spaces
  llm_canonicalization: future
```

## Public API / Methods

The architecture suggests these abstractions, without final method signatures:

- `LLMClient`
- `EmbeddingClient`
- `RerankerClient`
- `StructuredExtractionClient`

Exact Pydantic schema field constraints, enum names, and prompt schemas remain open implementation questions.

## Inputs

- normalized chunks from [storage-design.md](storage-design.md)
- chunk text and source references
- model configuration
- retrieval candidate text for reranking
- supporting chunks for answer generation in [qa-design.md](qa-design.md)

## Outputs

- chunk summaries
- chunk tags
- chunk entities
- document summaries
- document-level tags/entities
- entity summaries
- embeddings with dimension `1024`
- reranker scores
- answer-generation text used by Q&A services

## Side effects

Model clients should not write source files, graph nodes, or tool responses directly. Side effects are owned by calling services, such as processed JSON storage or answer generation.

## Testing requirements

Validate model behavior with:

- schema validation for extracted tags and entities;
- retries for invalid LLM JSON;
- embedding dimension checks against `1024`;
- reranker candidate-count checks using `top_k_before_rerank` and `top_k_after_rerank`;
- benchmark cases that measure failed extraction rate and invalid JSON rate;
- Q&A faithfulness checks that ensure answer generation uses supporting chunks.

## What this must not do

- Do not require external APIs for MVP.
- Do not use LLM-based canonicalization in MVP.
- Do not classify semantic concepts such as `invoice` or `budget` as `document_type`; use tags.
- Do not let model calls leak into parsers, graph sync, CLI wrappers, or LangChain tool wrappers.
- Do not silently accept invalid JSON extraction output.

## Extension points

- LLM-based canonicalization can be added later.
- Embeddings may be compressed in JSON later if storage grows too large.
- Search cache may be added after the first benchmark run.
- External model providers can be introduced later behind the same client boundaries.

## Dependencies

- LM Studio OpenAI-compatible endpoint at `http://localhost:1234/v1`
- `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- `mlx-lm`
- `Qwen/Qwen3-Embedding-0.6B`
- `Qwen/Qwen3-Reranker-0.6B`
- local `transformers` or `sentence-transformers`
- chunks and processed JSON from [storage-design.md](storage-design.md)
- retrieval scoring from [retrieval-design.md](retrieval-design.md)
- grounded answer generation from [qa-design.md](qa-design.md)

## Failure modes / risks

| Failure or risk | Mitigation |
|---|---|
| LLM extraction invalid JSON | retry with stricter prompt/schema |
| embedding failure | mark chunks as missing embedding |
| embedding model unavailable | retrieval falls back to keyword/entity/tag search |
| reranker unavailable | retrieval falls back to hybrid formula without reranker |
| weak extraction quality | validate on benchmark dataset |
| local model instability | schema validation + retries |
| hallucinated answers | Q&A answers only from supporting chunks |

## Validation

Validate model strategy by checking that:

- configured model names match this file;
- embeddings have dimension `1024`;
- embeddings are normalized when configured;
- full vectors are stored in JSON during MVP;
- chunk extraction returns schema-valid summaries, tags, and entities;
- normalization uses lowercase, trim, and collapse repeated spaces;
- document-level fields aggregate from chunks;
- semantic types remain tags, not `document_type`;
- model calls occur behind explicit client abstractions;
- invalid model outputs are visible in metrics and logs.

## Update rules

Update this file when model providers, model names, base URLs, embedding dimensions, reranker settings, extraction schemas, normalization rules, entity types, document type rules, model abstractions, model failure handling, or model validation requirements change.
