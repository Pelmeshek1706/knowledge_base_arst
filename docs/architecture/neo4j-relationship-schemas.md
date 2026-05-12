# Neo4j Relationship Schemas

## Purpose

This file defines MVP Neo4j relationship types, directions, cardinality, relationship properties, and deterministic relationship creation rules.

## When to read this

Read this file when changing graph edge types, relationship properties, duplicate/version behavior, deterministic `RELATED_TO` logic, graph sync relationship upserts, or traversal assumptions.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-node-schemas.md](neo4j-node-schemas.md)
- [neo4j-indexes.md](neo4j-indexes.md)
- [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md)
- [storage-design.md](storage-design.md)

## Source of truth

This file is authoritative for MVP Neo4j relationship contracts, relationship directions, cardinality, relationship metadata, duplicate/version edge rules, and deterministic `RELATED_TO` rules.

## Content

### Responsibility

Relationship schemas define how processed documents, chunks, tags, entities, types, duplicates, versions, and related documents are connected in Neo4j.

MVP relationship types:

```text
CONTAINS
HAS_TAG
HAS_TYPE
MENTIONS
DUPLICATE_OF
NEWER_VERSION_OF
RELATED_TO
```

### `(:Document)-[:CONTAINS]->(:Chunk)`

Represents document-to-chunk ownership.

#### Direction

```text
(:Document)-[:CONTAINS]->(:Chunk)
```

#### Cardinality

```text
Document 1 -> N Chunk
Chunk 1 -> 1 Document
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `chunk_index` | `INTEGER` | Same as `Chunk.chunk_index`. |
| `created_at` | `STRING` or `DATETIME` | Relationship creation time. |

### `(:Document)-[:HAS_TAG]->(:Tag)`

Represents document-level tag assignment.

#### Direction

```text
(:Document)-[:HAS_TAG]->(:Tag)
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | LLM/rule confidence. May be `1.0` or `null` in MVP. |
| `source` | `STRING` | `llm_extraction`, `rule_based`, `manual`. |
| `extraction_level` | `STRING` | `document`. |
| `source_chunk_ids` | `LIST<STRING>` | Chunks that contributed to document-level tag. |

### `(:Chunk)-[:HAS_TAG]->(:Tag)`

Represents chunk-level tag assignment.

#### Direction

```text
(:Chunk)-[:HAS_TAG]->(:Tag)
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | Confidence for this chunk-tag pair. |
| `source` | `STRING` | `llm_extraction`, `rule_based`, `manual`. |
| `extraction_level` | `STRING` | `chunk`. |

### `(:Document)-[:HAS_TYPE]->(:DocumentType)`

Represents extension-based type.

#### Direction

```text
(:Document)-[:HAS_TYPE]->(:DocumentType)
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `source` | `STRING` | `file_extension`. |
| `confidence` | `FLOAT` | Always `1.0` in MVP. |

### `(:Chunk)-[:MENTIONS]->(:Entity)`

Represents entity mentions in chunks.

#### Direction

```text
(:Chunk)-[:MENTIONS]->(:Entity)
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | Extraction confidence. |
| `source` | `STRING` | `llm_extraction`, `rule_based`, `manual`. |
| `mention_text` | `STRING?` | Exact or normalized mention text if available. |
| `count` | `INTEGER?` | Mention count in this chunk. |
| `extraction_level` | `STRING` | `chunk`. |

### `(:Document)-[:MENTIONS]->(:Entity)`

Represents aggregated document-level entity mention.

#### Direction

```text
(:Document)-[:MENTIONS]->(:Entity)
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | Aggregated confidence. |
| `source` | `STRING` | `aggregated_from_chunks`. |
| `source_chunk_ids` | `LIST<STRING>` | Chunks where this entity appeared. |
| `count` | `INTEGER?` | Total mention count if available. |
| `extraction_level` | `STRING` | `document`. |

### `(:Document)-[:DUPLICATE_OF]->(:Document)`

Represents exact duplicate document relation.

#### Direction rule

```text
(:DuplicateDocument)-[:DUPLICATE_OF]->(:CanonicalDocument)
```

#### Creation rule

Create only when exact duplicate is detected:

```text
different source_id
same raw_bytes_hash
OR
different source_id
same extracted_text_hash
```

MVP handles exact duplicates only.

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | `1.0` for exact duplicate. |
| `source` | `STRING` | `raw_bytes_hash`, `extracted_text_hash`, or `both`. |
| `raw_bytes_hash_match` | `BOOLEAN` | True if raw bytes hash matched. |
| `extracted_text_hash_match` | `BOOLEAN` | True if extracted text hash matched. |
| `created_at` | `STRING` or `DATETIME` | Relationship creation time. |

#### Canonical rule

Canonical document is selected by:

```text
newest modified_at
fallback newest ingested_at
```

### `(:Document)-[:NEWER_VERSION_OF]->(:Document)`

Represents changed file version relation.

#### Direction rule

```text
(:NewerDocument)-[:NEWER_VERSION_OF]->(:OlderDocument)
```

#### Creation rule

Create when:

```text
same source_id
different raw_bytes_hash or extracted_text_hash
```

For CLI without TTY or automated mode:

```text
auto NEWER_VERSION_OF
```

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | `1.0` for deterministic version relation. |
| `source` | `STRING` | `same_source_id_different_hash`. |
| `previous_modified_at` | `STRING` or `DATETIME?` | Older document modified time. |
| `new_modified_at` | `STRING` or `DATETIME?` | Newer document modified time. |
| `created_at` | `STRING` or `DATETIME` | Relationship creation time. |

### `(:Document)-[:RELATED_TO]->(:Document)`

Represents deterministic document relation.

#### Direction rule

For symmetric relations, create only one edge using deterministic ordering:

```text
lower(document_id) -> higher(document_id)
```

This prevents duplicate mirror edges.

#### MVP creation rules

Create `RELATED_TO` only from deterministic evidence:

```text
shared normalized tags
shared normalized entities
same DocumentType
duplicate/version neighborhood
high vector similarity between chunks/documents
```

Do not create LLM-inferred `RELATED_TO` in MVP.

#### Relationship properties

| Property | Type | Description |
|---|---:|---|
| `confidence` | `FLOAT` | Final deterministic relationship confidence. |
| `source` | `STRING` | `deterministic`. |
| `reason` | `STRING` | Human-readable reason. |
| `shared_tag_names` | `LIST<STRING>` | Tags shared by both documents. |
| `shared_entity_keys` | `LIST<STRING>` | Entity keys shared by both documents. |
| `shared_entity_names` | `LIST<STRING>` | Display names of shared entities. |
| `same_document_type` | `BOOLEAN` | True if same document type contributed. |
| `graph_score` | `FLOAT?` | Graph component score. |
| `tag_score` | `FLOAT?` | Tag component score. |
| `entity_score` | `FLOAT?` | Entity component score. |
| `vector_score` | `FLOAT?` | Vector/similarity component score. |
| `created_at` | `STRING` or `DATETIME` | Relationship creation time. |
| `updated_at` | `STRING` or `DATETIME` | Last update time. |

## Dependencies

- Node schemas from [neo4j-node-schemas.md](neo4j-node-schemas.md)
- Upsert templates from [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- Duplicate and version detection from [storage-design.md](storage-design.md)
- Retrieval query templates from [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md)

## Failure modes / risks

| Risk | Impact | Mitigation |
|---|---|---|
| Relationship duplication | Noisy graph traversal and bad related-document results | Use deterministic `MERGE` and application-level relation ordering. |
| Incorrect duplicate canonical direction | Wrong canonical document in search and Q&A | Use newest `modified_at`, then newest `ingested_at`. |
| LLM-inferred relationship creep | Untrusted graph links | Keep `RELATED_TO` deterministic in MVP. |
| Missing source chunk IDs on aggregated relations | Weak explainability | Preserve contributing chunk IDs on document-level tag/entity relations. |
| Stale relationship scores | Misleading retrieval ranking | Store persistent relation scores only; keep query scores in retrieval responses. |

## Validation

Validate relationship schemas by checking that:

- every chunk has exactly one owning `Document` through `CONTAINS`;
- document-level and chunk-level tags use distinct `extraction_level` values;
- document-level entity relations aggregate from chunk-level mentions where applicable;
- exact duplicate files create `DUPLICATE_OF` from duplicate to canonical document;
- changed same-source files create `NEWER_VERSION_OF` from newer to older document;
- `RELATED_TO` has only one deterministic edge per document pair;
- no LLM-inferred `RELATED_TO` edges are required in MVP.

## Update rules

Update this file when relationship types, directions, cardinality, relationship properties, duplicate/version rules, deterministic `RELATED_TO` logic, or relationship validation rules change.
