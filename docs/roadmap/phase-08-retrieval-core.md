# Phase 8: Retrieval Core

## Purpose

Implement deterministic, testable retrieval functions before exposing tools or
agent workflows.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 7: Neo4j Setup + Graph Sync](phase-07-neo4j-setup-graph-sync.md)

## Outputs

```text
personal_kb/retrieval/
  search_plan.py
  keyword_search.py
  entity_search.py
  tag_search.py
  vector_search.py
  graph_expansion.py
  hybrid_scoring.py
  retrieval_service.py
```

## In scope

- Keyword/title search.
- Entity search.
- Tag search.
- Vector search.
- Graph expansion.
- Hybrid scoring.
- Reranking after candidate pruning.
- Retrieval fallbacks when embedding/reranker is unavailable.
- Source references and matched chunk summaries in results.

## Out of scope

- LLM answer generation.
- Tool adapter implementation.
- LangGraph agent routing.

## Related docs

- [Roadmap index](index.md)
- [Retrieval design](../architecture/retrieval-design.md)
- [Tool contracts search plan](../implementation/tool-contracts/search-plan.md)
- [Tool contracts retrieval tools](../implementation/tool-contracts/retrieval-tools.md)
- [Phase 9: QA Service](phase-09-qa-service.md)
- [Phase 10: KnowledgeToolService + StructuredTools](phase-10-knowledge-tool-service-structured-tools.md)

## Source of truth

This file is authoritative for Phase 8 retrieval layer, pipeline, and
retrieval acceptance criteria roadmap scope.

## Implementation checklist

Required retrieval layers:

| Layer | Purpose |
|---|---|
| keyword/title search | exact file names, titles, obvious terms |
| entity search | documents/chunks mentioning entities |
| tag search | topic-based discovery |
| vector search | semantic chunk retrieval |
| graph expansion | related documents through relationships |
| hybrid scoring | combine layer scores |
| reranking | rerank candidate chunks/documents |

Default pipeline:

```text
exact keyword/title search
-> entity search
-> vector search over chunks
-> graph expansion around matched chunks/entities
-> reranking
```

## Exit criteria

- `search_documents` can return ranked documents with score breakdown.
- Retrieval works without LLM answer generation.
- Reranker is applied after candidate pruning.
- Retrieval can fall back if embedding/reranker is unavailable.
- Query results include source references and matched chunk summaries.

## Validation

- Run retrieval without answer generation.
- Confirm ranked documents include score breakdowns.
- Confirm reranker runs after candidate pruning.
- Disable embedding/reranker dependencies and confirm retrieval fallback
  behavior.
- Confirm query results include source references and matched chunk summaries.

## Failure modes / risks

- Poor retrieval quality is a high-risk failure mode; benchmark early and tune
  `SearchPlan` and scoring.
- Retrieval must not depend on Q&A generation.
- Missing fallbacks can make search unusable when local embedding or reranker
  dependencies are unavailable.

## Update rules

Update this file when retrieval layers, default pipeline, scoring behavior,
fallback rules, or source reference requirements change.
