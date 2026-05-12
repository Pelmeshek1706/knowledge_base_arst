# Neo4j Retrieval Queries

## Purpose

This file defines Neo4j query templates and graph-backed score mapping used by retrieval.

## When to read this

Read this file when changing Cypher retrieval templates, graph expansion behavior, full-text retrieval, vector retrieval, duplicate/version lookup queries, or mapping Neo4j graph signals into hybrid scoring.

## Related files

- [graph-schema.md](graph-schema.md)
- [retrieval-design.md](retrieval-design.md)
- [neo4j-node-schemas.md](neo4j-node-schemas.md)
- [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- [neo4j-indexes.md](neo4j-indexes.md)
- [model-strategy.md](model-strategy.md)

## Source of truth

This file is authoritative for graph retrieval Cypher templates, graph expansion templates, duplicate/version lookup queries, the Neo4j-backed hybrid score mapping, and the rule that query-specific scores are returned in retrieval responses rather than stored as graph truth.

## Content

### Responsibility

These query templates are used by retrieval services to search documents, chunks, tags, entities, vectors, related documents, duplicates, and version groups.

Higher-level retrieval order, ranking policy, output contracts, and failure handling are defined in [retrieval-design.md](retrieval-design.md).

### Get document with chunks

```cypher
MATCH (d:Document {document_id: $document_id})-[:CONTAINS]->(c:Chunk)
RETURN d, c
ORDER BY c.chunk_index ASC;
```

### Search by tag

```cypher
MATCH (t:Tag)
WHERE t.normalized_name CONTAINS $normalized_query
MATCH (d:Document)-[r:HAS_TAG]->(t)
RETURN d, t, r.confidence AS score
ORDER BY score DESC
LIMIT $top_k;
```

### Search by entity

```cypher
MATCH (e:Entity)
WHERE e.normalized_name CONTAINS $normalized_query
MATCH (d:Document)-[r:MENTIONS]->(e)
RETURN d, e, r.confidence AS score
ORDER BY score DESC
LIMIT $top_k;
```

### Full-text document search

```cypher
CALL db.index.fulltext.queryNodes('document_fulltext_idx', $query)
YIELD node, score
RETURN node AS document, score
ORDER BY score DESC
LIMIT $top_k;
```

### Full-text chunk search

```cypher
CALL db.index.fulltext.queryNodes('chunk_fulltext_idx', $query)
YIELD node, score
MATCH (d:Document)-[:CONTAINS]->(node)
RETURN d AS document, node AS chunk, score
ORDER BY score DESC
LIMIT $top_k;
```

### Vector search over chunks

```cypher
CALL db.index.vector.queryNodes(
  'chunk_embedding_vector_idx',
  $top_k,
  $query_embedding
)
YIELD node, score
MATCH (d:Document)-[:CONTAINS]->(node)
RETURN
  d AS document,
  node AS chunk,
  score AS vector_score
ORDER BY vector_score DESC;
```

### Graph expansion around matched chunks

```cypher
MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
WHERE c.chunk_id IN $chunk_ids

OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(related_chunk:Chunk)<-[:CONTAINS]-(related_doc:Document)
WHERE related_doc.document_id <> d.document_id

OPTIONAL MATCH (c)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(related_doc_by_tag:Document)
WHERE related_doc_by_tag.document_id <> d.document_id

RETURN
  d,
  c,
  collect(DISTINCT e) AS shared_entities,
  collect(DISTINCT t) AS shared_tags,
  collect(DISTINCT related_doc) + collect(DISTINCT related_doc_by_tag) AS related_documents;
```

### Show related documents

```cypher
MATCH (d:Document {document_id: $document_id})
OPTIONAL MATCH (d)-[r:RELATED_TO]-(related:Document)
RETURN related, r
ORDER BY r.confidence DESC
LIMIT $top_k;
```

### Find duplicates

```cypher
MATCH (d:Document)-[r:DUPLICATE_OF]->(canonical:Document)
RETURN d AS duplicate, canonical, r
ORDER BY d.file_path ASC;
```

### Find latest version group

```cypher
MATCH path = (newer:Document)-[:NEWER_VERSION_OF*0..]->(older:Document)
WHERE newer.document_id = $document_id OR older.document_id = $document_id
RETURN path;
```

### Hybrid search mapping

The graph supports the hybrid formula:

```text
final_score =
  0.25 * graph_score
+ 0.20 * vector_score
+ 0.15 * entity_score
+ 0.10 * tag_score
+ 0.10 * title_keyword_score
+ 0.20 * reranker_score
```

Score sources:

| Score | Graph source |
|---|---|
| `graph_score` | `RELATED_TO`, shared neighbors, graph expansion |
| `vector_score` | `chunk_embedding_vector_idx` |
| `entity_score` | `MENTIONS` relation confidence/count |
| `tag_score` | `HAS_TAG` relation confidence |
| `title_keyword_score` | `document_fulltext_idx` |
| `reranker_score` | Local reranker output, not stored unless debug is enabled |

Storage decision:

Do not store every query-level score in Neo4j.

Store only persistent relation scores:

```text
RELATED_TO.confidence
HAS_TAG.confidence
MENTIONS.confidence
```

Query-specific scores belong in the `SearchDocumentsResponse`.

## Public API / Methods

These templates support retrieval methods behind:

- CLI `kb search`;
- CLI `kb ask` when retrieval context is needed;
- `RetrievalService`;
- `KnowledgeToolService`;
- LangChain `StructuredTool` wrappers;
- future MCP adapters.

## Inputs

- `document_id`
- `normalized_query`
- full-text `$query`
- `$top_k`
- `$query_embedding`
- `$chunk_ids`
- Neo4j indexes from [neo4j-indexes.md](neo4j-indexes.md)

## Outputs

- documents;
- chunks;
- tags;
- entities;
- related documents;
- duplicate/canonical document pairs;
- version paths;
- graph/vector/full-text scores used by the retrieval layer.

## Side effects

These queries should be read-only. They must not mutate Neo4j, processed JSON, or source files.

## Testing requirements

Test these queries against a small populated graph to verify:

- document lookup returns chunks in `chunk_index` order;
- tag and entity searches return confidence scores;
- full-text indexes can query documents and chunks;
- vector query uses `chunk_embedding_vector_idx`;
- graph expansion excludes the original document from related-document candidates;
- duplicate and version queries return expected paths.

## What this must not do

- Do not store query-specific scores in Neo4j as persistent truth.
- Do not write graph changes from retrieval queries.
- Do not return unbounded chunks without `top_k` limits.
- Do not bypass retrieval warnings for low confidence or conflicting results.

## Dependencies

- Full-text and vector indexes from [neo4j-indexes.md](neo4j-indexes.md)
- Relationship contracts from [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- Retrieval scoring and output contracts from [retrieval-design.md](retrieval-design.md)
- Local embeddings and reranker from [model-strategy.md](model-strategy.md)

## Failure modes / risks

| Risk | Impact | Mitigation |
|---|---|---|
| Full-text index missing | Keyword/title search fails | Validate index existence during setup. |
| Vector index missing or wrong dimension | Vector search fails | Use `chunk_embedding_vector_idx` with dimension `1024`. |
| Query-specific scores stored as graph truth | Stale score data | Store query scores in `SearchDocumentsResponse`, not Neo4j. |
| Graph expansion returns too many related documents | Slow or noisy retrieval | Apply top-k limits and reranking in retrieval services. |
| Duplicate/version traversal is ambiguous | Confusing document lineage | Preserve required edge directions in [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md). |

## Validation

Validate these templates by checking that:

- every index name referenced here is created in [neo4j-indexes.md](neo4j-indexes.md);
- vector queries use `chunk_embedding_vector_idx`;
- graph expansion uses `MENTIONS` and `HAS_TAG` relationships consistently with [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md);
- persistent scores are limited to `RELATED_TO.confidence`, `HAS_TAG.confidence`, and `MENTIONS.confidence`;
- retrieval services return query-specific scores in the response object.

## Update rules

Update this file when Neo4j query templates, index names, retrieval graph expansion behavior, score source mapping, duplicate/version lookup behavior, or query score storage rules change.
