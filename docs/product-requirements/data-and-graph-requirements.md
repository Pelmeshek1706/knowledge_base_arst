# Data and Graph Requirements

## Purpose

This file defines Product Requirements for manifest entries, processed document JSON, chunk data, Neo4j MVP nodes, relationships, and deterministic `RELATED_TO` rules.

## When to read this

Read this when changing storage contracts, document JSON shape, manifest shape, graph schema, relationship rules, or graph rebuild behavior.

## Related files

- [Product requirements index](index.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Validation and acceptance](validation-and-acceptance.md)
- [Technical architecture](../../Technical_Architecture_Personal_KB_v0.3.md)
- [Neo4j graph schema](../../Neo4j_Graph_Schema_Personal_KB_v0.1.md)

## Source of truth

This file is authoritative for Product Requirements data and graph requirements.

## Content

## Data Requirements

### Manifest Entry

Each document must have a manifest entry with at least:

```json
{
  "document_id": "uuid",
  "source_id": "relative/path/to/file.pdf",
  "file_path": "relative/path/to/file.pdf",
  "file_name": "file.pdf",
  "file_extension": "pdf",
  "raw_bytes_hash": "sha256...",
  "extracted_text_hash": "sha256...",
  "processed_json_path": "kb_storage/documents/uuid.json",
  "status": "processed | failed | skipped",
  "ingested_at": "...",
  "modified_at": "...",
  "neo4j_synced": true,
  "canonical_document_id": "uuid",
  "duplicate_of": null,
  "newer_version_of": null,
  "error": null
}
```

### Processed Document JSON

Each processed document JSON must include:

- `schema_version`
- `document`
- `raw_text`
- `chunks`
- `relationships`
- `processing`
- model metadata
- parser metadata
- embedding metadata

### Chunk Data

Each chunk must include:

- `chunk_id`
- `document_id`
- `chunk_index`
- `text`
- `summary`
- `tags`
- `entities`
- `source_ref`
- `embedding`

## Graph Requirements

### MVP Nodes

```text
(:Document)
(:Chunk)
(:Entity)
(:Tag)
(:DocumentType)
```

### MVP Relationships

```text
(:Document)-[:CONTAINS]->(:Chunk)
(:Document)-[:HAS_TAG]->(:Tag)
(:Chunk)-[:HAS_TAG]->(:Tag)
(:Document)-[:HAS_TYPE]->(:DocumentType)
(:Chunk)-[:MENTIONS]->(:Entity)
(:Document)-[:MENTIONS]->(:Entity)
(:Document)-[:DUPLICATE_OF]->(:Document)
(:Document)-[:NEWER_VERSION_OF]->(:Document)
(:Document)-[:RELATED_TO]->(:Document)
```

### Deterministic RELATED_TO Rules

`RELATED_TO` may be created from deterministic signals only:

- shared normalized tags;
- shared normalized entities;
- same document type;
- duplicate/version neighborhood;
- high chunk/document similarity after vector threshold or reranking.

No LLM-inferred `RELATED_TO` relationships are required in MVP.

## Responsibility

This file owns the required product-level shape of persisted document data and graph data.

## Component boundaries

- Manifest and processed JSON are the rebuildable source for Neo4j state.
- Graph sync reads processed JSON and upserts nodes and relationships.
- Search and Q&A consume graph/vector state and stored chunks but must not redefine storage contracts.

## Data flow

1. Local documents are discovered and hashed.
2. Parser and model processing produce raw text, chunks, summaries, tags, entities, and embeddings.
3. Processed state is persisted in `kb_storage/manifest.json` and `kb_storage/documents/<document_id>.json`.
4. Graph sync reads processed JSON and upserts Neo4j nodes and relationships.
5. Search and Q&A use graph/vector state and source references.

## Design decisions

- JSON is primary processed storage.
- Neo4j must be rebuildable from processed JSON without repeating parsing/extraction/embedding.
- `RELATED_TO` relationships are deterministic in MVP.
- LLM-inferred relationships are future-only.

## Trade-offs

- Full embeddings in JSON increase storage size but preserve rebuildability.
- Deterministic relationships limit semantic richness but reduce hallucinated or unstable graph links.
- Separate duplicate/version document nodes preserve history but require canonical document handling.

## Inputs

- Parsed raw text.
- Chunk summaries, tags, entities, source refs, and embeddings.
- Manifest state and hashes.

## Outputs

- `kb_storage/manifest.json`
- `kb_storage/documents/<document_id>.json`
- Neo4j `Document`, `Chunk`, `Entity`, `Tag`, and `DocumentType` nodes.
- Neo4j `CONTAINS`, `HAS_TAG`, `HAS_TYPE`, `MENTIONS`, `DUPLICATE_OF`, `NEWER_VERSION_OF`, and `RELATED_TO` relationships.

## Testing requirements

- Validate manifest entries include required fields.
- Validate processed document JSON includes required top-level objects and metadata.
- Validate chunks include full `text`, summaries, tags, entities, source refs, and embeddings.
- Validate graph sync creates only MVP node and relationship types unless explicitly changed.
- Validate `RELATED_TO` is created only from deterministic signals in MVP.

## What this must not do

- Must not store absolute file paths in JSON.
- Must not require Neo4j state that cannot be rebuilt from processed JSON.
- Must not require LLM-inferred `RELATED_TO` relationships in MVP.
- Must not omit full chunk text needed for Q&A.

## Extension points

- Future source-specific graph nodes.
- Future FAQ/QA memory nodes.
- Future LLM-inferred relationship types.
- Future external source normalization into internal `RawDocument` and `ProcessedDocument` contracts.

## Dependencies

- `kb_storage/manifest.json`
- `kb_storage/documents/<document_id>.json`
- Neo4j database, default `knowledge_base3`, fallback `neo4j`
- Graph sync service
- Search/Q&A services

## Failure modes / risks

- Missing required manifest or processed JSON fields can break ingestion, rebuild, or search.
- Storing absolute paths breaks portability.
- Omitting full chunk text breaks Q&A requirements.
- LLM-inferred relationships in MVP can introduce unstable graph edges.
- Neo4j schema drift can break graph sync.

## Risks and mitigations

- Use versioned schemas and idempotent upserts to mitigate schema drift.
- Use deterministic canonical rules for duplicate/version confusion.
- Use validation before graph sync to prevent malformed JSON from creating incomplete graph state.

## Validation

- Validate JSON schema for manifest and processed document files.
- Rebuild Neo4j from processed JSON without rerunning parser/model steps.
- Inspect sample graph data for required nodes and relationships.
- Confirm no LLM-inferred `RELATED_TO` edge is required for MVP.

## Validation strategy

Use schema validation, graph sync integration tests, and rebuild tests that start from `kb_storage/` only.

## Update rules

- Update this file when manifest, processed JSON, chunk, graph node, graph relationship, or deterministic relationship rules change.
- Update [functional-requirements.md](functional-requirements.md) when storage or graph changes affect ingestion or graph sync.
- Update [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md) when graph/storage changes affect query output.
