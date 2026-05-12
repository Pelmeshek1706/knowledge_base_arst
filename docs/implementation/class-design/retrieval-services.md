# Retrieval Services

## Purpose

This file defines the retrieval service classes for `personal_kb`: search plan execution, candidate merging, graph/vector/entity/tag/keyword layers, hybrid scoring, reranking, and structured search results.

## When to read this

Read this when changing:

- `RetrievalService` behavior;
- search subservice ownership;
- search layer priority or result merging;
- scoring formulas or weights;
- reranker integration;
- search result shape or warnings.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [graph-services.md](graph-services.md)
- [model-extraction-services.md](model-extraction-services.md)
- [qa-services.md](qa-services.md)
- [tool-services.md](tool-services.md)
- [../../architecture/retrieval-design.md](../../architecture/retrieval-design.md)

## Source of truth

This file is authoritative for retrieval orchestration, search subservices, scoring, and reranking class design.

## Content

### `RetrievalService`

**File:** `retrieval/retrieval_service.py`

Responsibility:

- Execute configurable search plan.
- Merge candidates from keyword/entity/tag/vector/graph layers.
- Apply scoring and reranking.
- Return structured search results.

```python
class RetrievalService:
    def search_documents(self, request: SearchDocumentsRequest) -> SearchDocumentsResponse:
        ...
```

Dependencies:

```text
GraphService
EmbeddingClient
RerankerClient
ScoringService
```

### Search subservices

| Class | Responsibility |
|---|---|
| `KeywordSearchService` | title/path/text keyword retrieval through Neo4j indexes |
| `EntitySearchService` | entity-name based retrieval |
| `TagSearchService` | tag-based retrieval |
| `VectorSearchService` | chunk embedding similarity search |
| `GraphExpansionService` | expand around matched docs/chunks/entities/tags |
| `ScoringService` | compute hybrid scores and score breakdown |

### `ScoringService`

**File:** `retrieval/scoring.py`

Formula without reranker:

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

```python
class ScoringService:
    def compute_score(self, candidate: RetrievalCandidate, weights: dict[str, float]) -> ScoreBreakdown: ...
```

## Public API / Methods

- `RetrievalService.search_documents`
- `ScoringService.compute_score`
- Search subservices for keyword, entity, tag, vector, and graph expansion behavior.

## Inputs

- `SearchDocumentsRequest`.
- `SearchPlan`.
- Query text.
- Search config weights.
- Graph candidates from `GraphService`.
- Query embeddings from `EmbeddingClient`.
- Reranker scores from `RerankerClient`.

## Outputs

- `SearchDocumentsResponse`.
- Ranked `SearchDocumentResult` records.
- `ScoreBreakdown` values.
- Matched chunks, matched entities, related documents, and warnings.

## Side effects

- Queries Neo4j through `GraphService`.
- Calls local embedding model through `EmbeddingClient`.
- Calls local reranker through `RerankerClient`.
- Does not write processed JSON, mutate Neo4j, or generate final answers.

## Dependencies

- `SearchDocumentsRequest`, `SearchDocumentsResponse`, `SearchDocumentResult`, `MatchedChunk`, and `ScoreBreakdown` from [schemas.md](schemas.md).
- `GraphService` from [graph-services.md](graph-services.md).
- `EmbeddingClient` and `RerankerClient` from [model-extraction-services.md](model-extraction-services.md).
- `QAService` consumes retrieval results in [qa-services.md](qa-services.md).
- `KnowledgeToolService.search_documents` delegates to retrieval in [tool-services.md](tool-services.md).

## Failure modes / risks

- One retrieval layer may fail while others can still provide partial results.
- Missing embeddings can reduce vector search coverage.
- Reranker failure should produce warnings or fallback behavior rather than corrupt result shape.
- Score weights must remain explainable through `ScoreBreakdown`.
- Retrieval must not hallucinate answers; it returns evidence candidates only.

## Validation

- Unit-test `ScoringService` formula correctness with and without reranker.
- Verify candidate merging preserves source refs and matched chunks.
- Verify search by tag/entity returns expected documents.
- Verify vector search returns expected chunks.
- Verify warnings are returned for partial fallback.

## Testing requirements

- Unit-test search plan execution branches.
- Unit-test scoring weights and final score.
- Integration-test keyword/entity/tag/vector retrieval against Neo4j.
- Benchmark retrieval with:
  - `Recall@K`;
  - `Precision@K`;
  - `MRR`;
  - `Hit Rate`;
  - `nDCG@K`;
  - latency.

## What this must not do

- `RetrievalService` must not generate final answers.
- `RetrievalService` must not depend on LangGraph or LangChain StructuredTool.
- `RerankerClient` must not retrieve candidates.
- Search subservices must not mutate source files or processed JSON.

## Extension points

- Add new search layers by extending `SearchLayer`, the subservice list, merge behavior, and tests together.
- Add alternate scoring modes through `ScoreMode`.
- Add richer graph expansion after preserving current result contracts.

## Update rules

Update this file whenever retrieval layers, search plan behavior, scoring formulas, weights, reranking, result construction, warnings, or retrieval validation changes.
