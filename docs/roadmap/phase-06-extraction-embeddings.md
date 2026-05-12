# Phase 6: Extraction + Embeddings

## Purpose

Generate chunk/document summaries, tags, entities, entity summaries, and
vectors.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 5: Local Model Clients](phase-05-local-model-clients.md)

## Outputs

```text
personal_kb/ingestion/
  extraction_service.py
  embedding_service.py
  document_aggregation_service.py
```

## In scope

- Chunk summaries.
- Chunk tags.
- Chunk entities.
- Chunk embeddings.
- Document-level aggregation.
- Document summaries.
- Document tags/entities/entity summaries.
- Processed JSON updates.
- Entity/tag normalization with lowercase + trim + collapse spaces.
- Retry and failure status for invalid LLM output.

## Out of scope

- Neo4j sync.
- Retrieval scoring.
- Q&A answer generation.
- Required LLM-inferred document relationships.

## Related docs

- [Roadmap index](index.md)
- [Model strategy](../architecture/model-strategy.md)
- [Storage design](../architecture/storage-design.md)
- [Phase 7: Neo4j Setup + Graph Sync](phase-07-neo4j-setup-graph-sync.md)
- [Phase 8: Retrieval Core](phase-08-retrieval-core.md)

## Source of truth

This file is authoritative for Phase 6 extraction, embedding, aggregation, and
processed JSON update roadmap scope.

## Implementation checklist

Extraction sequence:

```text
Chunk text
-> chunk summary
-> chunk tags
-> chunk entities
-> chunk embedding
-> document-level aggregation
-> document summary
-> document tags/entities/entity summaries
-> processed JSON update
```

## Exit criteria

- Each chunk receives summary, tags, entities, and embedding.
- Document-level tags/entities are aggregated from chunks.
- Entity/tag normalization uses lowercase + trim + collapse spaces.
- Embeddings are stored both in JSON and Neo4j later.
- Invalid LLM output is handled with retry and failure status.

## Validation

- Run extraction over representative chunks and confirm summaries, tags,
  entities, and embeddings are present.
- Confirm document-level tags/entities aggregate from chunks.
- Confirm normalization uses lowercase + trim + collapse spaces.
- Confirm embeddings are stored in processed JSON for later Neo4j sync.
- Trigger invalid LLM output and confirm retry plus failure status behavior.

## Failure modes / risks

- Model output invalid JSON is a high-risk failure mode; mitigate with Pydantic
  validation, retries, and failed status.
- Slow local models require cached processed JSON and unchanged-file skip
  behavior.
- Missing embeddings here blocks vector search and graph vector index sync.

## Update rules

Update this file when extraction sequence, normalized metadata behavior,
embedding persistence, or invalid-output handling changes.
