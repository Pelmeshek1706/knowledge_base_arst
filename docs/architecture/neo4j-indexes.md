# Neo4j Constraints and Indexes

## Purpose

This file defines Neo4j constraints, standard indexes, full-text indexes, and the chunk vector index for the `personal_kb` MVP.

## When to read this

Read this file when changing `kb setup-db`, schema initialization, Neo4j 5 constraint syntax, lookup indexes, full-text search indexes, vector index dimensions, or index validation.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-node-schemas.md](neo4j-node-schemas.md)
- [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- [neo4j-setup-sync.md](neo4j-setup-sync.md)
- [neo4j-validation-risks.md](neo4j-validation-risks.md)
- [model-strategy.md](model-strategy.md)

## Source of truth

This file is authoritative for Neo4j uniqueness constraints, standard indexes, full-text indexes, vector index configuration, vector dimensions, and index compatibility notes.

## Content

### Responsibility

Neo4j indexes support graph sync idempotency, duplicate/version detection, keyword retrieval, entity/tag lookup, and vector search over chunks.

### Constraints

Use Neo4j 5 style syntax.

```cypher
CREATE CONSTRAINT document_document_id_unique IF NOT EXISTS
FOR (d:Document)
REQUIRE d.document_id IS UNIQUE;

CREATE CONSTRAINT chunk_chunk_id_unique IF NOT EXISTS
FOR (c:Chunk)
REQUIRE c.chunk_id IS UNIQUE;

CREATE CONSTRAINT tag_normalized_name_unique IF NOT EXISTS
FOR (t:Tag)
REQUIRE t.normalized_name IS UNIQUE;

CREATE CONSTRAINT entity_entity_key_unique IF NOT EXISTS
FOR (e:Entity)
REQUIRE e.entity_key IS UNIQUE;

CREATE CONSTRAINT document_type_name_unique IF NOT EXISTS
FOR (dt:DocumentType)
REQUIRE dt.name IS UNIQUE;
```

Notes:

- Avoid node property existence constraints in MVP for maximum compatibility.
- Validate required fields in Pydantic before graph sync.
- Do not use Enterprise-only node key constraints in MVP.

### Standard indexes

```cypher
CREATE INDEX document_source_id_idx IF NOT EXISTS
FOR (d:Document)
ON (d.source_id);

CREATE INDEX document_file_path_idx IF NOT EXISTS
FOR (d:Document)
ON (d.file_path);

CREATE INDEX document_raw_bytes_hash_idx IF NOT EXISTS
FOR (d:Document)
ON (d.raw_bytes_hash);

CREATE INDEX document_extracted_text_hash_idx IF NOT EXISTS
FOR (d:Document)
ON (d.extracted_text_hash);

CREATE INDEX document_content_hash_idx IF NOT EXISTS
FOR (d:Document)
ON (d.content_hash);

CREATE INDEX document_processing_status_idx IF NOT EXISTS
FOR (d:Document)
ON (d.processing_status);

CREATE INDEX document_canonical_document_id_idx IF NOT EXISTS
FOR (d:Document)
ON (d.canonical_document_id);

CREATE INDEX chunk_document_id_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.document_id);

CREATE INDEX chunk_chunk_index_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.chunk_index);

CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity)
ON (e.type);

CREATE INDEX entity_normalized_name_idx IF NOT EXISTS
FOR (e:Entity)
ON (e.normalized_name);

CREATE INDEX entity_type_normalized_name_idx IF NOT EXISTS
FOR (e:Entity)
ON (e.type, e.normalized_name);
```

### Full-text indexes

Full-text indexes support keyword/title/chunk search before vector retrieval and reranking.

```cypher
CREATE FULLTEXT INDEX document_fulltext_idx IF NOT EXISTS
FOR (d:Document)
ON EACH [d.title, d.normalized_title, d.file_name, d.summary];

CREATE FULLTEXT INDEX chunk_fulltext_idx IF NOT EXISTS
FOR (c:Chunk)
ON EACH [c.text, c.summary, c.section, c.sheet];

CREATE FULLTEXT INDEX tag_fulltext_idx IF NOT EXISTS
FOR (t:Tag)
ON EACH [t.name, t.normalized_name];

CREATE FULLTEXT INDEX entity_fulltext_idx IF NOT EXISTS
FOR (e:Entity)
ON EACH [e.name, e.normalized_name, e.summary];
```

### Vector index

The MVP uses a Neo4j vector index over `Chunk.embedding`.

Embedding model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Dimension:

```text
1024
```

Similarity:

```text
cosine
```

Cypher:

```cypher
CREATE VECTOR INDEX chunk_embedding_vector_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
```

Notes:

- Store embedding as a `LIST<FLOAT>` property in MVP.
- Also store full embedding arrays in processed JSON.
- Keep `embedding_model` and `embedding_dimension` on every chunk.
- If Neo4j version supports native `VECTOR` type, keep MVP on `LIST<FLOAT>` unless there is a clear performance reason to migrate.

## Dependencies

- Node property definitions from [neo4j-node-schemas.md](neo4j-node-schemas.md)
- Setup execution flow from [neo4j-setup-sync.md](neo4j-setup-sync.md)
- Retrieval behavior from [retrieval-design.md](retrieval-design.md)
- Embedding model and dimension from [model-strategy.md](model-strategy.md)

## Failure modes / risks

| Risk | Impact | Mitigation |
|---|---|---|
| Required properties are not validated before sync | Bad writes or missing lookup keys | Validate required fields in Pydantic before graph sync. |
| Enterprise-only constraints are used | Setup failure on Community deployments | Do not use node key constraints in MVP. |
| Vector index dimension mismatch | Vector search failure | Use `1024` consistently on chunk embeddings and the vector index. |
| Full-text indexes are missing | Keyword and title search degrade | Include full-text index creation in `kb setup-db`. |
| Index status is not verified | Setup can appear successful while indexes are unavailable | Verify index status after setup. |

## Validation

Validate constraints and indexes by running:

- `SHOW CONSTRAINTS;`
- `SHOW INDEXES;`

Schema is ready only when:

- constraints exist for `Document.document_id`, `Chunk.chunk_id`, `Tag.normalized_name`, `Entity.entity_key`, and `DocumentType.name`;
- standard indexes exist for source IDs, hashes, chunk document IDs, and entity lookups;
- full-text indexes exist for documents, chunks, tags, and entities;
- vector index exists for `Chunk.embedding` with dimension `1024`.

Detailed verification queries are in [neo4j-validation-risks.md](neo4j-validation-risks.md).

## Update rules

Update this file when uniqueness rules, lookup fields, full-text fields, vector index configuration, embedding dimension, Neo4j syntax, or schema setup validation changes.
