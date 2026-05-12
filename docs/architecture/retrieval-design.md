# Retrieval Design

## Purpose

This file defines the architecture for document search, search planning, retrieval layers, graph expansion, hybrid scoring, reranking, search output contracts, search logging, search failure handling, and retrieval validation.

## When to read this

Read this file when changing `search_documents`, search plans, retrieval layers, score weights, reranking, candidate selection, related-document expansion, search result JSON, search logs, search metrics, or search failure behavior.

## Related files

- [overview.md](overview.md)
- [storage-design.md](storage-design.md)
- [graph-schema.md](graph-schema.md)
- [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md)
- [model-strategy.md](model-strategy.md)
- [qa-design.md](qa-design.md)
- [agent-design.md](agent-design.md)

## Source of truth

This file is authoritative for the default search pipeline, configurable search plans, search layers, hybrid scoring formulas, reranking configuration, score breakdown output, `search_documents` output, retrieval metrics, search logs, search failure modes, and future search extensions.

## Content

### Responsibility

Search is agentic at query time, but individual retrieval functions should be deterministic and testable.

The retrieval layer must:

- search documents, chunks, tags, and entities;
- support graph-first or vector-first search plans;
- combine keyword, entity, tag, vector, graph, and reranker signals;
- produce explainable score breakdowns;
- return structured JSON for CLI, LangChain StructuredTools, and future MCP adapters;
- limit top-k chunks to avoid context overload.

### Component boundaries

Retrieval should not:

- ingest documents;
- parse files;
- mutate source files;
- update graph schema;
- implement LangChain wrapper logic;
- generate final grounded answers without the Q&A layer;
- hide low-confidence or conflicting-document warnings.

Graph traversal and vector search use Neo4j as defined in [graph-schema.md](graph-schema.md), with exact Cypher templates in [neo4j-retrieval-queries.md](neo4j-retrieval-queries.md). Reranking uses the local reranker in [model-strategy.md](model-strategy.md). Q&A behavior is defined in [qa-design.md](qa-design.md).

### Default search pipeline

```text
exact keyword/title search
-> entity search
-> vector search over chunks
-> graph expansion around matched chunks/entities
-> reranking
```

`search_plan.priority` can override this order, including graph-first mode.

### Configurable search plan

```json
{
  "query": "documents about accounting and budget",
  "search_plan": {
    "search_objects": ["document", "entity", "tag", "chunk"],
    "priority": ["graph", "tag", "vector", "keyword"],
    "top_k": 10,
    "reranker": "Qwen/Qwen3-Reranker-0.6B",
    "score_mode": "hybrid_formula_with_reranker",
    "include_related_documents": true,
    "include_chunks": true
  }
}
```

### Search layers

| Layer | Purpose |
|---|---|
| keyword/title search | catch exact document names and obvious terms |
| entity search | find documents mentioning extracted entities |
| tag search | find documents by normalized topics |
| vector search | semantic matching over chunks using Qwen3 embeddings |
| graph expansion | find related documents through entities/tags/relationships |
| reranking | reorder candidates using Qwen3 local reranker |

### Hybrid formula

Base explainable formula:

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

All weights must be configurable.

### Reranking config

```yaml
reranking:
  model_name: Qwen/Qwen3-Reranker-0.6B
  top_k_before_rerank: 50
  top_k_after_rerank: 8
```

### Score breakdown output

```json
{
  "confidence": 0.87,
  "score_breakdown": {
    "graph_score": 0.91,
    "vector_score": 0.83,
    "entity_score": 0.88,
    "tag_score": 0.75,
    "title_keyword_score": 0.62,
    "reranker_score": 0.89,
    "final_score": 0.87
  }
}
```

### `search_documents` output

```json
{
  "query": "documents about accounting and budgets",
  "search_mode": ["graph", "tags", "vector"],
  "results": [
    {
      "document_id": "doc_123",
      "title": "Budget 2025.xlsx",
      "file_path": "data/budget_2025.xlsx",
      "document_type": "spreadsheet",
      "summary": "Contains yearly budget planning and accounting notes.",
      "tags": ["budget", "accounting", "invoice"],
      "created_at": "2025-12-01",
      "modified_at": "2026-01-15",
      "confidence": 0.87,
      "score_breakdown": {
        "graph_score": 0.91,
        "vector_score": 0.83,
        "entity_score": 0.88,
        "tag_score": 0.75,
        "title_keyword_score": 0.62,
        "reranker_score": 0.89,
        "final_score": 0.87
      },
      "matched_entities": ["Budget", "Accounting"],
      "matched_chunks": [
        {
          "chunk_id": "chunk_7",
          "source_ref": {
            "file_path": "data/budget_2025.xlsx",
            "page": null,
            "section": null,
            "sheet": "Budget",
            "cell_range": "A1:F40"
          },
          "summary": "Contains budget table and account categories.",
          "reason": "Contains budget table and account categories."
        }
      ],
      "related_documents": [
        {
          "document_id": "doc_456",
          "relationship": "RELATED_TO",
          "confidence": 0.78
        }
      ]
    }
  ]
}
```

### Search configuration

```yaml
search:
  default_top_k: 10
  include_related_documents: true
  include_chunks: true
  score_mode: hybrid_formula_with_reranker
  weights:
    graph_score: 0.25
    vector_score: 0.20
    entity_score: 0.15
    tag_score: 0.10
    title_keyword_score: 0.10
    reranker_score: 0.20
```

### Search logs

Log:

- query
- search_plan
- candidate counts per layer
- reranker scores
- final selected documents
- latency per step
- warnings

### Future search extensions

Future retrieval layers:

```text
FAQ/QA memory search
source-specific search: Jira / Confluence / Gmail / Google Drive
temporal search by dates/deadlines
decision-log search
person-centric search
project-centric search
contradiction detection
staleness detection
```

Future search pipeline:

```text
FAQ memory search
-> exact/title search
-> entity search
-> graph traversal
-> vector search
-> source-specific retrieval
-> reranking
-> answer generation with citations
-> optional save/update FAQ entry
```

## Public API / Methods

This file defines the behavior of the `search_documents` capability exposed through:

- CLI `kb search`
- LangChain `StructuredTool` wrappers
- future MCP server adapter

The implementation should live in core services such as `RetrievalService`, called through `KnowledgeToolService` as described in [agent-design.md](agent-design.md).

## Inputs

- user query
- optional `search_plan`
- processed document/chunk/tag/entity data in Neo4j
- embeddings from [model-strategy.md](model-strategy.md)
- graph relationships from [graph-schema.md](graph-schema.md)
- retrieval configuration

## Outputs

- ranked documents
- matched chunks
- matched entities
- related documents
- confidence
- score breakdown
- warnings when confidence is low or conflicts are detected

## Side effects

Search should not mutate source documents or run ingestion. Search logs may be written to `kb_storage/logs/search.log`.

## Testing requirements

Retrieval metrics:

- Recall@K
- Precision@K
- MRR
- Hit Rate
- nDCG@K

Search must be tested against the JSONL benchmark in [overview.md](overview.md), including top-10 expected-document checks.

## What this must not do

- Do not require external APIs for MVP search.
- Do not make scoring weights hard-coded only; all weights must be configurable.
- Do not return unbounded chunks for document lookup.
- Do not perform source writes or ingestion from retrieval functions.
- Do not hide warnings for low confidence or conflicting documents.

## Extension points

- FAQ/QA memory search
- source-specific search for Jira, Confluence, Gmail, and Google Drive
- temporal search by dates/deadlines
- decision-log search
- person-centric search
- project-centric search
- contradiction detection
- staleness detection
- search cache after the first benchmark run

## Dependencies

- Neo4j graph and vector index from [graph-schema.md](graph-schema.md)
- processed JSON and chunk/source references from [storage-design.md](storage-design.md)
- embeddings and reranker from [model-strategy.md](model-strategy.md)
- `KnowledgeToolService` from [agent-design.md](agent-design.md)
- grounded answer consumer in [qa-design.md](qa-design.md)

## Failure modes / risks

| Failure | Mitigation |
|---|---|
| Neo4j unavailable | return system error |
| embedding model unavailable | fallback to keyword/entity/tag search |
| reranker unavailable | fallback to hybrid formula without reranker |
| no results | return empty result with explanation |
| low confidence | return warning |
| conflicting documents | return warnings and source list |
| slow search | cache embeddings, top-k limits, reranker only after candidate pruning |

## Validation

Validate retrieval by checking that:

- default search follows keyword/title, entity, vector, graph expansion, reranking order;
- `search_plan.priority` can override order, including graph-first mode;
- all configured search layers are represented in score breakdowns when used;
- hybrid weights are configurable;
- reranker uses `top_k_before_rerank: 50` and `top_k_after_rerank: 8`;
- document lookup returns chunk summaries and source references, not unbounded full text;
- benchmark questions return expected documents in top-10;
- search latency target is around 10 seconds for document lookup and relationship retrieval on the initial dataset;
- search logs include query, search_plan, candidate counts, reranker scores, selected documents, latency, and warnings.

## Update rules

Update this file when search plans, retrieval layers, score formulas, score weights, reranker configuration, search result schemas, search logging, retrieval metrics, failure modes, or future search extensions change.
