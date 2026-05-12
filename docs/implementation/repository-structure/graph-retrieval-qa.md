# Graph, Retrieval, And Q&A

## Purpose

This file defines the repository areas for Neo4j setup/sync, graph query services, hybrid retrieval, scoring, reranking, and source-grounded Q&A.

## When to read this

Read this when implementing or changing `personal_kb/graph/`, `personal_kb/retrieval/`, or `personal_kb/qa/`.

## Related files

- [ingestion-parsing-models.md](ingestion-parsing-models.md)
- [tools-agent-adapters.md](tools-agent-adapters.md)
- [../class-design/graph-services.md](../class-design/graph-services.md)
- [../class-design/retrieval-services.md](../class-design/retrieval-services.md)
- [../class-design/qa-services.md](../class-design/qa-services.md)
- [../../architecture/graph-schema.md](../../architecture/graph-schema.md)
- [../../architecture/retrieval-design.md](../../architecture/retrieval-design.md)
- [../../architecture/qa-design.md](../../architecture/qa-design.md)

## Source of truth

This file is authoritative for repository structure and responsibilities of graph, retrieval, and Q&A modules. Detailed graph schema and retrieval behavior are owned by the architecture and class-design files linked above.

## Content

## `personal_kb/graph/`

Purpose:

- Neo4j connection, schema setup, graph sync, graph queries.

### `neo4j_driver.py`

Responsibilities:

- create Neo4j driver;
- connect to configured database `knowledge_base3`;
- fallback to `neo4j` if needed;
- expose session helpers.

### `schema_manager.py`

Responsibilities:

- implement `kb setup-db`;
- create constraints;
- create indexes;
- create vector index with dimension `1024`;
- avoid APOC.

Must support:

```text
primary mode: kb setup-db
optional mode: --auto-setup-db
```

### `graph_sync_service.py`

Responsibilities:

- read `ProcessedDocument` from JSON;
- upsert `Document`, `Chunk`, `Entity`, `Tag`, `DocumentType`;
- upsert relationships;
- write sync status back to manifest.

Must not:

- parse files;
- call LLM;
- generate embeddings;
- decide chunking.

### `graph_service.py`

Responsibilities:

- read/query graph during retrieval;
- expose graph operations for services;
- hide Cypher details from higher layers.

Used by:

- retrieval service;
- document service;
- duplicate service;
- relationship explanation.

## `personal_kb/retrieval/`

Purpose:

- implement hybrid search;
- deterministic and testable;
- no LangGraph-specific logic.

### `search_plan_builder.py`

Responsibilities:

- build default `SearchPlan`;
- adapt plan based on query type;
- allow user/tool-provided override.

### `retrieval_service.py`

Responsibilities:

- main search orchestration;
- execute search layers;
- merge candidates;
- score;
- rerank;
- return structured search results.

Uses:

- keyword search;
- entity search;
- tag search;
- vector search;
- graph expansion;
- scoring;
- reranking.

### `scoring.py`

Responsibilities:

- implement hybrid formula.

Base formula:

```text
final_score =
  0.35 * graph_score
+ 0.25 * vector_score
+ 0.20 * entity_score
+ 0.10 * tag_score
+ 0.10 * title_keyword_score
```

Formula with reranker:

```text
final_score =
  0.25 * graph_score
+ 0.20 * vector_score
+ 0.15 * entity_score
+ 0.10 * tag_score
+ 0.10 * title_keyword_score
+ 0.20 * reranker_score
```

## `personal_kb/qa/`

Purpose:

- answer user questions using retrieved chunks/documents;
- keep answers source-grounded.

### `qa_service.py`

Responsibilities:

- orchestrate Q&A;
- call retrieval service if needed;
- build context;
- call answer generator;
- validate answer;
- return source documents and supporting chunks.

### `context_builder.py`

Responsibilities:

- select supporting chunks;
- enforce top-k limits;
- include text only when query requires document text;
- include summary/source refs for document lookup.

### `citation_builder.py`

Responsibilities:

- attach source refs;
- include file path/page/section/sheet/cell range;
- ensure answers are traceable.

## Dependencies

- `kb_storage/documents/<document_id>.json`
- `kb_storage/manifest.json`
- Neo4j database `knowledge_base3`
- Neo4j fallback database `neo4j`
- `personal_kb/models/embedding_client.py`
- `personal_kb/models/reranker_client.py`
- `personal_kb/models/llm_client.py`
- `personal_kb/schemas/search.py`
- `personal_kb/schemas/qa.py`

## Failure modes / risks

- Graph sync can become non-rebuildable if it depends on parsing, LLM calls, or embedding generation.
- Retrieval can become non-deterministic if LangGraph-specific logic enters retrieval services.
- Cypher details can leak above `GraphService`.
- Incorrect vector dimension breaks the Neo4j vector index; the required dimension is `1024`.
- Q&A can hallucinate if answer validation and citations are bypassed.

## Validation

- `kb setup-db` creates constraints, indexes, and the `1024`-dimension vector index.
- `kb ingest data` creates Neo4j nodes and relationships from processed JSON.
- `kb search "some topic" --json` returns ranked documents with confidence and source refs.
- `kb ask "question about a document" --json` returns an answer, source documents, and supporting chunks.
- Retrieval scoring unit tests cover base formula and reranker formula.

## Update rules

Update this file when graph setup/sync responsibilities, database names, vector dimensions, retrieval layers, scoring weights, reranker policy, Q&A grounding, or citation requirements change.
