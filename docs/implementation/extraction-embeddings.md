# Extraction and Embeddings

## Purpose

This document captures the Phase 6 extraction input/output contract for chunk
metadata, chunk embeddings, and document-level aggregation.

## Extraction flow

1. Parse the source file into normalized raw text.
2. Chunk the text into `ChunkRecord` items with `source_ref`.
3. Run chunk extraction in `non_thinking` mode with strict JSON Schema output
   using the dedicated extraction model config.
4. If a compatible LM Studio reasoning model returns empty visible assistant
   content but valid JSON in `reasoning_content`, the model client may use the
   configured reasoning-content fallback only after the JSON validates against
   the requested Pydantic schema.
5. Validate the structured output and write `summary`, `tags`, and `entities`
   onto each chunk.
6. Generate chunk embeddings and store `embedding`, `embedding_model`, and
   `embedding_dimension`.
7. Aggregate chunk metadata into document-level `summary`, `tags`, and
   `entities`.

## Chunk extraction output contract

The live Qwen2.5-backed chunk extraction call returns a validated payload with
summary, free-form retrieval tags, and typed entities:

```json
{
  "summary": "Concise grounded summary.",
  "tags": ["Budget Review", "Roadmap", "Neo4j"],
  "entities": [
    {
      "name": "Budget Review",
      "type": "Topic",
      "confidence": 0.86
    },
    {
      "name": "Neo4j",
      "type": "Technology"
    }
  ]
}
```

Rules enforced in code:

- output must satisfy strict JSON Schema validation;
- `summary` must not be blank;
- tag strings are trimmed, normalized with lowercase + trim + collapse spaces,
  and deduplicated by normalized name before becoming `TagRecord` records;
- entity objects must include `name` and `type`; `confidence` is optional;
- entity names are trimmed, normalized with lowercase + trim + collapse spaces,
  deduplicated by `(type, normalized_name)`, and converted into `EntityRecord`
  objects with deterministic IDs/keys;
- tag records use `source="llm_extraction"` and the current chunk ID in
  `source_chunks`;
- entity records use `source="llm_extraction"` and the current chunk ID in
  `source_chunks`;
- extraction uses `thinking_mode="non_thinking"`;
- reasoning-content fallback is allowed only when visible assistant content is
  empty, the reasoning text is valid JSON, and the parsed payload validates
  against the requested schema; fallback usage is surfaced in response metadata
  and warnings.

## Full example

The example below uses the entire document text as input. The embedding vector is
shortened to 3 dimensions because this example is backed by deterministic test
fixtures; production embeddings remain 1024-dimensional.

### Input text

```text
Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.
```

### Structured output

```json
{
  "document": {
    "document_id": "doc-1",
    "summary": "The note focuses on a budget review and roadmap planning sequence.",
    "tags": [
      {
        "name": "Budget Review",
        "normalized_name": "budget review",
        "confidence": 0.9,
        "source": "llm_extraction",
        "source_chunks": ["doc-1-0"]
      },
      {
        "name": "Roadmap",
        "normalized_name": "roadmap",
        "confidence": 0.8,
        "source": "llm_extraction",
        "source_chunks": ["doc-1-0"]
      }
    ],
    "entities": []
  },
  "chunks": [
    {
      "chunk_id": "doc-1-0",
      "summary": "Alpha beta gamma delta outline the budget and roadmap topics.",
      "tags": [
        {
          "name": "Budget Review",
          "normalized_name": "budget review",
          "confidence": 0.9,
          "source": "llm_extraction",
          "source_chunks": ["doc-1-0"]
        },
        {
          "name": "Roadmap",
          "normalized_name": "roadmap",
          "confidence": 0.8,
          "source": "llm_extraction",
          "source_chunks": ["doc-1-0"]
        }
      ],
      "entities": [
        {
          "name": "Alpha",
          "normalized_name": "alpha",
          "type": "Topic",
          "confidence": 0.76,
          "source": "llm_extraction",
          "source_chunks": ["doc-1-0"]
        }
      ],
      "embedding": [1.0, 0.0, 0.0],
      "embedding_model": "test-embedding",
      "embedding_dimension": 3
    }
  ]
}
```
