# Phase 5: Local Model Clients

## Purpose

Create model boundaries before implementing extraction, embedding, reranking,
and Q&A.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 4: Chunking + Processed JSON](phase-04-chunking-processed-json.md)

## Outputs

```text
personal_kb/models/
  llm_client.py
  embedding_client.py
  reranker_client.py
  structured_extraction_client.py
```

## In scope

- LM Studio OpenAI-compatible LLM client.
- Local embedding client.
- Local reranker client.
- Structured extraction client.
- Mockable model boundaries.
- Lazy model loading.
- Schema validation and retry behavior for structured LLM output.

## Out of scope

- Chunk extraction implementation.
- Retrieval scoring.
- Q&A prompt implementation.
- Model loading during module import.

## Related docs

- [Roadmap index](index.md)
- [Model strategy](../architecture/model-strategy.md)
- [Phase 6: Extraction + Embeddings](phase-06-extraction-embeddings.md)
- [Phase 9: QA Service](phase-09-qa-service.md)

## Source of truth

This file is authoritative for Phase 5 model client roadmap scope and model
runtime decisions.

## Implementation checklist

Model decisions:

| Component | Model/runtime |
|---|---|
| LLM | LM Studio OpenAI-compatible endpoint at `http://localhost:1234/v1` |
| LLM model | `mlx-community/Qwen3.5-9B-OptiQ-4bit` |
| Embedding | `Qwen/Qwen3-Embedding-0.6B`, dimension `1024` |
| Reranker | `Qwen/Qwen3-Reranker-0.6B` |
| Embedding execution | `transformers` or `sentence-transformers` locally |
| Reranker execution | `transformers` or `sentence-transformers` locally |

## Exit criteria

- Model clients are testable with mocks.
- No model loading happens during module import.
- Embeddings are normalized when configured.
- Reranker accepts query-document/chunk pairs and returns scores.
- LLM structured output is schema-validated and retried on invalid JSON.

## Validation

- Unit-test model clients with mocks.
- Import modules and confirm no model loading occurs.
- Test embedding normalization when configured.
- Test reranker scoring over query-document/chunk pairs.
- Test invalid structured LLM JSON triggers schema validation and retry.

## Failure modes / risks

- Slow local models can make ingestion and Q&A unusable without caching and
  skip behavior.
- Import-time model loading can make CLI startup and tests brittle.
- Invalid JSON from model output must be schema-validated and retried.

## Update rules

Update this file when local model choices, client boundaries, lazy-loading
rules, or structured output validation rules change.
