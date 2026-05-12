# Phase 1: Schemas + Config + Manifest

## Purpose

Define stable data contracts before implementing ingestion, graph sync, tools,
or retrieval.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 0: Project Bootstrap](phase-00-project-bootstrap.md)

## Outputs

```text
personal_kb/schemas/
  config.py
  document.py
  chunk.py
  entity.py
  tag.py
  manifest.py
  search.py
  qa.py
  tools.py

personal_kb/core/
  config_loader.py
  paths.py
  normalization.py

personal_kb/storage/
  manifest_store.py
  processed_document_store.py
```

## In scope

- Runtime configuration schemas.
- Document, chunk, entity, and tag schemas.
- Manifest schemas and persistent manifest behavior.
- Search, Q&A, and tool request/response schemas.
- Core config loading, path, and normalization helpers.
- Manifest and processed document store modules.

## Out of scope

- Raw file discovery and hashing.
- Parsing and chunking.
- Graph sync.
- Retrieval, Q&A, tools, and agent behavior.

## Related docs

- [Roadmap index](index.md)
- [Class design schemas](../implementation/class-design/schemas.md)
- [Storage design](../architecture/storage-design.md)
- [Tool contracts](../implementation/tool-contracts/index.md)

## Source of truth

This file is authoritative for Phase 1 schema, config, manifest, and storage
contract roadmap scope. Detailed schema design belongs in
[class design schemas](../implementation/class-design/schemas.md).

## Implementation checklist

Required schemas:

| Schema | Purpose |
|---|---|
| `AppConfig` | Full runtime configuration. |
| `Neo4jConfig` | Neo4j URI, database, fallback database, setup mode. |
| `ModelConfig` | LLM, embedding, reranker model configs. |
| `DocumentRecord` | Document-level processed object. |
| `ChunkRecord` | Chunk-level processed object. |
| `EntityRecord` | Entity with type, confidence, source, normalization fields. |
| `TagRecord` | Tag with confidence, source, normalized name. |
| `Manifest` | Global processed state index. |
| `ManifestDocumentEntry` | Per-document manifest metadata. |
| `SearchPlan` | Defines how a query should be searched. |
| `SearchDocumentsRequest` | Public request contract for document search. |
| `SearchDocumentsResponse` | Public response contract for document search. |
| `AnswerQuestionRequest` | Public request contract for Q&A. |
| `AnswerQuestionResponse` | Public response contract for Q&A. |

The manifest must track:

- `document_id`
- relative `source_id`
- relative `file_path`
- file extension
- raw bytes hash
- extracted text hash
- processing status
- error message if failed
- path to processed JSON
- Neo4j sync status
- duplicate/version metadata
- timestamps

## Exit criteria

- Schemas validate sample payloads.
- Invalid manifest entries fail validation clearly.
- Failed documents can be stored with `status="failed"` and error details.
- Relative path handling works from project root.
- No service logic depends on raw dictionaries.

## Validation

- Validate representative schema payloads.
- Validate invalid manifest entries and confirm clear errors.
- Persist a failed document manifest entry with `status="failed"` and error
  details.
- Confirm services consume typed schemas rather than raw dictionaries.

## Failure modes / risks

- Service logic depending on raw dictionaries can weaken validation guarantees.
- Missing failed-document state can make retry behavior ambiguous in later
  ingestion phases.
- Incorrect relative path handling can break portability from the project root.

## Update rules

Update this file when schema deliverables, manifest requirements, or contract
validation requirements change.
