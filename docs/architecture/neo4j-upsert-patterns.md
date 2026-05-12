# Neo4j Upsert Patterns

## Purpose

This file preserves the idempotent Cypher upsert templates used by `GraphSyncService`.

## When to read this

Read this file when implementing or changing graph sync write methods, debugging duplicate graph writes, updating relationship metadata writes, or translating processed JSON into Neo4j nodes and relationships.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-node-schemas.md](neo4j-node-schemas.md)
- [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- [neo4j-setup-sync.md](neo4j-setup-sync.md)
- [neo4j-indexes.md](neo4j-indexes.md)

## Source of truth

This file is authoritative for MVP Cypher upsert templates for documents, chunks, document types, tags, entities, duplicate edges, version edges, and deterministic related-document edges.

## Content

### Responsibility

Graph sync upsert methods must translate validated processed JSON into Neo4j graph state using deterministic `MERGE` patterns.

### Upsert Document

```cypher
MERGE (d:Document {document_id: $document_id})
SET
  d.source_id = $source_id,
  d.source_type = $source_type,
  d.file_path = $file_path,
  d.file_name = $file_name,
  d.file_extension = $file_extension,
  d.document_type = $document_type,
  d.title = $title,
  d.normalized_title = $normalized_title,
  d.summary = $summary,
  d.raw_bytes_hash = $raw_bytes_hash,
  d.extracted_text_hash = $extracted_text_hash,
  d.content_hash = $content_hash,
  d.created_at = $created_at,
  d.modified_at = $modified_at,
  d.ingested_at = $ingested_at,
  d.processing_status = $processing_status,
  d.is_duplicate = $is_duplicate,
  d.canonical_document_id = $canonical_document_id,
  d.schema_version = $schema_version,
  d.parser = $parser,
  d.chunker = $chunker,
  d.llm_model = $llm_model,
  d.embedding_model = $embedding_model,
  d.embedding_dimension = $embedding_dimension,
  d.tag_names = $tag_names,
  d.entity_names = $entity_names,
  d.updated_at = datetime()
RETURN d;
```

### Upsert Chunk

```cypher
MATCH (d:Document {document_id: $document_id})
MERGE (c:Chunk {chunk_id: $chunk_id})
SET
  c.document_id = $document_id,
  c.chunk_index = $chunk_index,
  c.text = $text,
  c.summary = $summary,
  c.file_path = $file_path,
  c.page = $page,
  c.section = $section,
  c.sheet = $sheet,
  c.cell_range = $cell_range,
  c.source_ref_json = $source_ref_json,
  c.embedding = $embedding,
  c.embedding_model = $embedding_model,
  c.embedding_dimension = $embedding_dimension,
  c.char_count = $char_count,
  c.token_count = $token_count,
  c.tag_names = $tag_names,
  c.entity_names = $entity_names,
  c.updated_at = datetime()
MERGE (d)-[r:CONTAINS]->(c)
SET
  r.chunk_index = $chunk_index,
  r.updated_at = datetime()
RETURN c;
```

### Upsert DocumentType

```cypher
MATCH (d:Document {document_id: $document_id})
MERGE (dt:DocumentType {name: $document_type})
SET
  dt.normalized_name = $document_type
MERGE (d)-[r:HAS_TYPE]->(dt)
SET
  r.source = 'file_extension',
  r.confidence = 1.0,
  r.updated_at = datetime()
RETURN dt;
```

### Upsert Tag and HAS_TAG

#### Document-level tag

```cypher
MATCH (d:Document {document_id: $document_id})
MERGE (t:Tag {normalized_name: $normalized_name})
SET
  t.tag_id = $tag_id,
  t.name = $name,
  t.updated_at = datetime()
MERGE (d)-[r:HAS_TAG]->(t)
SET
  r.confidence = $confidence,
  r.source = $source,
  r.extraction_level = 'document',
  r.source_chunk_ids = $source_chunk_ids,
  r.updated_at = datetime()
RETURN t;
```

#### Chunk-level tag

```cypher
MATCH (c:Chunk {chunk_id: $chunk_id})
MERGE (t:Tag {normalized_name: $normalized_name})
SET
  t.tag_id = $tag_id,
  t.name = $name,
  t.updated_at = datetime()
MERGE (c)-[r:HAS_TAG]->(t)
SET
  r.confidence = $confidence,
  r.source = $source,
  r.extraction_level = 'chunk',
  r.updated_at = datetime()
RETURN t;
```

### Upsert Entity and MENTIONS

#### Document-level entity

```cypher
MATCH (d:Document {document_id: $document_id})
MERGE (e:Entity {entity_key: $entity_key})
SET
  e.entity_id = $entity_id,
  e.name = $name,
  e.normalized_name = $normalized_name,
  e.type = $type,
  e.summary = $summary,
  e.updated_at = datetime()
MERGE (d)-[r:MENTIONS]->(e)
SET
  r.confidence = $confidence,
  r.source = 'aggregated_from_chunks',
  r.source_chunk_ids = $source_chunk_ids,
  r.count = $count,
  r.extraction_level = 'document',
  r.updated_at = datetime()
RETURN e;
```

#### Chunk-level entity

```cypher
MATCH (c:Chunk {chunk_id: $chunk_id})
MERGE (e:Entity {entity_key: $entity_key})
SET
  e.entity_id = $entity_id,
  e.name = $name,
  e.normalized_name = $normalized_name,
  e.type = $type,
  e.summary = coalesce($summary, e.summary),
  e.updated_at = datetime()
MERGE (c)-[r:MENTIONS]->(e)
SET
  r.confidence = $confidence,
  r.source = $source,
  r.mention_text = $mention_text,
  r.count = $count,
  r.extraction_level = 'chunk',
  r.updated_at = datetime()
RETURN e;
```

### Upsert DUPLICATE_OF

```cypher
MATCH (dup:Document {document_id: $duplicate_document_id})
MATCH (canon:Document {document_id: $canonical_document_id})
MERGE (dup)-[r:DUPLICATE_OF]->(canon)
SET
  r.confidence = 1.0,
  r.source = $source,
  r.raw_bytes_hash_match = $raw_bytes_hash_match,
  r.extracted_text_hash_match = $extracted_text_hash_match,
  r.updated_at = datetime(),
  dup.is_duplicate = true,
  dup.canonical_document_id = $canonical_document_id
RETURN r;
```

### Upsert NEWER_VERSION_OF

```cypher
MATCH (newer:Document {document_id: $newer_document_id})
MATCH (older:Document {document_id: $older_document_id})
MERGE (newer)-[r:NEWER_VERSION_OF]->(older)
SET
  r.confidence = 1.0,
  r.source = 'same_source_id_different_hash',
  r.previous_modified_at = $previous_modified_at,
  r.new_modified_at = $new_modified_at,
  r.updated_at = datetime(),
  newer.canonical_document_id = $newer_document_id,
  older.canonical_document_id = $newer_document_id
RETURN r;
```

### Upsert RELATED_TO

```cypher
MATCH (a:Document {document_id: $source_document_id})
MATCH (b:Document {document_id: $target_document_id})
WHERE a.document_id <> b.document_id
MERGE (a)-[r:RELATED_TO]->(b)
SET
  r.confidence = $confidence,
  r.source = 'deterministic',
  r.reason = $reason,
  r.shared_tag_names = $shared_tag_names,
  r.shared_entity_keys = $shared_entity_keys,
  r.shared_entity_names = $shared_entity_names,
  r.same_document_type = $same_document_type,
  r.graph_score = $graph_score,
  r.tag_score = $tag_score,
  r.entity_score = $entity_score,
  r.vector_score = $vector_score,
  r.updated_at = datetime()
RETURN r;
```

Application code must enforce deterministic ordering:

```text
source_document_id = min(doc_a, doc_b)
target_document_id = max(doc_a, doc_b)
```

## Inputs

- Validated processed JSON document records.
- Validated chunk records with embeddings and source references.
- Normalized tags and entities.
- Duplicate/version metadata from ingestion.
- Deterministic related-document evidence.

## Outputs

- Upserted `Document`, `Chunk`, `DocumentType`, `Tag`, and `Entity` nodes.
- Upserted `CONTAINS`, `HAS_TYPE`, `HAS_TAG`, `MENTIONS`, `DUPLICATE_OF`, `NEWER_VERSION_OF`, and `RELATED_TO` relationships.

## Side effects

These Cypher statements mutate Neo4j graph state. They must not mutate source files, re-run parsing, call LLMs, or generate embeddings.

## Testing requirements

Graph sync tests should verify:

- each upsert can run repeatedly without duplicating nodes;
- each relationship upsert can run repeatedly without duplicating edges;
- chunk upsert fails clearly when parent document is missing;
- tag and entity upserts preserve normalized uniqueness;
- duplicate/version upserts set `canonical_document_id` correctly;
- `RELATED_TO` input ordering is enforced before running the Cypher.

## What this must not do

- Do not use APOC.
- Do not use non-deterministic relationship directions.
- Do not create mirror `RELATED_TO` edges.
- Do not create `Summary`, `Section`, or source-specific nodes in MVP upserts.
- Do not store query-specific retrieval scores as graph truth.

## Dependencies

- Node schemas from [neo4j-node-schemas.md](neo4j-node-schemas.md)
- Relationship schemas from [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- Constraints and indexes from [neo4j-indexes.md](neo4j-indexes.md)
- Graph sync boundaries from [neo4j-setup-sync.md](neo4j-setup-sync.md)

## Failure modes / risks

| Risk | Impact | Mitigation |
|---|---|---|
| Missing parent document for chunk | Chunk upsert fails | Upsert document before chunks and report missing parent clearly. |
| Relationship mirror duplication | Noisy graph and inflated traversal scores | Enforce deterministic `source_document_id`/`target_document_id` ordering in application code. |
| Tag/entity normalization mismatch | Duplicate tag/entity nodes | Normalize before upsert and rely on uniqueness constraints. |
| Retrying partial sync creates duplicates | Graph drift | Use `MERGE` on stable IDs and deterministic keys. |
| Query-level scores are written into persistent relations | Stale graph score data | Only persistent relation scores belong on graph relationships. |

## Validation

Validate upsert patterns by running graph sync twice on the same processed JSON and confirming:

- node counts do not increase on the second run;
- relationship counts do not increase on the second run;
- updated properties are refreshed with current values;
- duplicate and version relationships still point in the required direction;
- `RELATED_TO` uses one edge per pair;
- `SHOW CONSTRAINTS` and `SHOW INDEXES` match [neo4j-indexes.md](neo4j-indexes.md).

## Update rules

Update this file when `GraphSyncService` write methods, Cypher parameters, node/relationship property names, idempotency rules, or deterministic relationship ordering changes.
