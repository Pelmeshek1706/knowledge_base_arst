# Neo4j Validation and Risks

## Purpose

This file defines schema verification queries, MVP schema acceptance criteria, and graph schema risks with mitigations.

## When to read this

Read this file when validating Neo4j setup, checking graph sync health, reviewing MVP readiness, debugging schema drift, or assessing graph schema risks.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-indexes.md](neo4j-indexes.md)
- [neo4j-setup-sync.md](neo4j-setup-sync.md)
- [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md)
- [retrieval-design.md](retrieval-design.md)

## Source of truth

This file is authoritative for Neo4j schema verification queries, MVP acceptance criteria for schema readiness, graph schema risks, and mitigations.

## Content

### Responsibility

Validation confirms that Neo4j contains the expected schema objects and graph data shape after setup and graph sync.

### List constraints

```cypher
SHOW CONSTRAINTS;
```

### List indexes

```cypher
SHOW INDEXES;
```

### Count nodes

```cypher
MATCH (n)
RETURN labels(n) AS labels, count(*) AS count
ORDER BY count DESC;
```

### Count relationships

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC;
```

### Check orphan chunks

```cypher
MATCH (c:Chunk)
WHERE NOT EXISTS {
  MATCH (:Document)-[:CONTAINS]->(c)
}
RETURN c.chunk_id, c.file_path
LIMIT 50;
```

### Check missing embeddings

```cypher
MATCH (c:Chunk)
WHERE c.embedding IS NULL OR c.embedding_dimension <> 1024
RETURN c.chunk_id, c.document_id, c.file_path
LIMIT 50;
```

### Check duplicate tag nodes

```cypher
MATCH (t:Tag)
WITH t.normalized_name AS normalized_name, count(*) AS count
WHERE count > 1
RETURN normalized_name, count;
```

### Check duplicate entity nodes

```cypher
MATCH (e:Entity)
WITH e.entity_key AS entity_key, count(*) AS count
WHERE count > 1
RETURN entity_key, count;
```

### MVP acceptance criteria for schema

The schema is ready when:

1. `kb setup-db` can run repeatedly without errors.
2. Constraints exist for:
   - `Document.document_id`;
   - `Chunk.chunk_id`;
   - `Tag.normalized_name`;
   - `Entity.entity_key`;
   - `DocumentType.name`.
3. Standard indexes exist for source IDs, hashes, chunk document IDs, and entity lookups.
4. Full-text indexes exist for documents, chunks, tags, and entities.
5. Vector index exists for `Chunk.embedding` with dimension `1024`.
6. A sample document can be synced from processed JSON into Neo4j.
7. Re-running graph sync does not duplicate nodes or relationships.
8. Duplicate documents are represented as separate `Document` nodes connected by `DUPLICATE_OF`.
9. Changed files are represented as separate `Document` nodes connected by `NEWER_VERSION_OF`.
10. Retrieval queries can return documents, chunks, tags, entities, and related documents.

### Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Schema too complex too early | Slow MVP | Use five MVP node labels only. |
| Relationship duplication | Noisy graph | Use deterministic `MERGE` and application-level relation ordering. |
| Tag/entity inconsistency | Weak search | Normalize with lowercase/trim/collapse spaces. |
| Vector index dimension mismatch | Vector search failure | Store `embedding_dimension = 1024` and validate before sync. |
| Neo4j Community database limitation | Setup failure with `knowledge_base3` | Fallback to `neo4j`. |
| Storing large chunk text in Neo4j | Larger database size | Accept for MVP; move text to JSON-only later if needed. |
| LLM extraction noise | Bad graph links | Benchmark and allow manual/future canonicalization. |
| Query-specific scores stored as graph truth | Stale score data | Store query scores in response, not graph. |

## Dependencies

- Setup/index definitions from [neo4j-indexes.md](neo4j-indexes.md)
- Setup and graph sync behavior from [neo4j-setup-sync.md](neo4j-setup-sync.md)
- Upsert behavior from [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- Retrieval query templates from [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md)
- Retrieval benchmark expectations from [retrieval-design.md](retrieval-design.md)

## Failure modes / risks

This file is itself the source of truth for schema risks. When a risk spans multiple graph files, keep the full risk table here and link to this file from the focused file that owns the behavior.

## Validation

Validate this documentation by checking that:

- every verification query references existing MVP labels, relationships, or properties;
- every acceptance criterion maps to a setup, graph sync, or retrieval behavior described in focused docs;
- every schema risk has a mitigation;
- validation still excludes future labels that are not implemented in MVP.

## Update rules

Update this file when schema verification queries, MVP acceptance criteria, graph readiness checks, risk descriptions, mitigations, or validation gates change.
