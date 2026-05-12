# Search Plan

## Purpose

This file defines the `SearchPlan` configuration contract and the `SearchPlanBuilder` service used by retrieval, Q&A, and agent routing.

## When to read this

Read this when changing:

- retrieval strategy fields;
- default search behavior;
- search layer priorities;
- reranker selection;
- score mode behavior;
- query-type-specific plans;
- validation rules for search plans.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [retrieval-tools.md](retrieval-tools.md)
- [qa-tools.md](qa-tools.md)
- [langchain-structured-tools.md](langchain-structured-tools.md)

## Source of truth

This file is authoritative for the `SearchPlan` schema, default search plan, allowed planning responsibilities, and `SearchPlanBuilder` methods.

## Content

### `SearchPlan`

`SearchPlan` is a configuration object that tells the system how to search, not what to search.

The user query defines what to search:

```text
"Where is WP2 described?"
```

The `SearchPlan` defines how the system should execute the search:

```text
- search documents, tags, entities, and chunks
- run keyword/entity/vector/graph search layers
- use reranker
- return top 10 documents
- include related documents
- include matched chunks
```

#### Why `SearchPlan` exists

Different questions need different retrieval strategies.

| Query | Better retrieval behavior |
|---|---|
| `Find document_a.docx` | title/path keyword-first |
| `Where was WP2 discussed?` | keyword + entity + vector + graph expansion |
| `Who is Penelope?` | entity search + graph search + Q&A |
| `Documents about budgets` | tag/entity/graph-heavy search |
| `How are doc A and doc B related?` | direct graph relationship lookup |

Without `SearchPlan`, search logic becomes hardcoded and difficult to tune.

#### Typical schema

```python
class SearchPlan(BaseModel):
    search_objects: list[SearchObject]
    priority: list[SearchLayer]
    top_k: int
    reranker: str | None
    score_mode: ScoreMode
    include_related_documents: bool
    include_chunks: bool
    filters: SearchFilters | None = None
```

#### Fields

| Field | Type | Purpose | Used by |
|---|---|---|---|
| `search_objects` | list | Selects object types: document/entity/tag/chunk | `RetrievalService` |
| `priority` | list | Search layer order: keyword/entity/tag/vector/graph | `RetrievalService` |
| `top_k` | int | Maximum final results | `RetrievalService`, `RerankerService` |
| `reranker` | string/null | Selects reranker mode/model | `RetrievalService`, `RerankerClient` |
| `score_mode` | enum | Selects hybrid formula mode | `ScoringService` |
| `include_related_documents` | bool | Include graph neighbors in output | `GraphService`, `RetrievalService` |
| `include_chunks` | bool | Include matched chunks in output | `RetrievalService` |
| `filters` | object/null | Optional source/date/type filters | `RetrievalService`, `GraphService` |

#### Default plan

```json
{
  "search_objects": ["document", "entity", "tag", "chunk"],
  "priority": ["keyword", "entity", "vector", "graph"],
  "top_k": 10,
  "reranker": "local_cross_encoder",
  "score_mode": "hybrid_formula_with_reranker",
  "include_related_documents": true,
  "include_chunks": true
}
```

#### Important rule

`SearchPlan` must not contain business logic. It is configuration only.

### `SearchPlanBuilder`

`SearchPlanBuilder` creates default or query-specific search plans.

#### Dependencies

```text
Config
Optional QueryClassifier
```

#### Methods

##### `build_default()`

Purpose: create the default retrieval strategy.

Used by:

```text
RetrievalService.search_documents when request.search_plan is None
LangGraph SearchPlanNode
```

##### `build_for_query_type(query_type)`

Purpose: create a plan optimized for a specific query class.

Examples:

| Query type | Plan behavior |
|---|---|
| `document_lookup` | keyword/title/entity first |
| `document_qa` | vector/chunk retrieval first |
| `entity_lookup` | entity/graph first |
| `relationship_explanation` | graph first |
| `duplicate_lookup` | duplicate graph/hash lookup |

Used by:

```text
LangGraph SearchPlanNode
```

##### `validate(search_plan)`

Purpose: validate that search objects, layers, score modes, and top-k values are supported.

Used by:

```text
RetrievalService.search_documents
KnowledgeToolService request validation
```

## Dependencies

- `Config`
- Optional `QueryClassifier`
- `RetrievalService`
- `KnowledgeToolService`
- LangGraph `SearchPlanNode`
- `RerankerClient`
- `ScoringService`
- `GraphService`

## Failure modes / risks

- `SearchPlan` contains unsupported values.
- `SearchPlan` includes business logic instead of configuration.
- Defaults become hardcoded inside retrieval methods instead of being built centrally.
- Query-type plans drift from LangGraph route names.

## Validation

Validate this contract with tests for:

- `SearchPlan` validation;
- `SearchPlanBuilder.build_default()`;
- `SearchPlanBuilder.build_for_query_type(query_type)`;
- `SearchPlanBuilder.validate(search_plan)`;
- `RetrievalService.search_documents` default-plan behavior when `request.search_plan is None`.

## Update rules

Update this file whenever `SearchPlan` fields, default values, validation rules, query type names, query-specific plan behavior, score modes, search layers, or reranker options change.

## Public API / Methods

- `SearchPlan`
- `SearchPlanBuilder.build_default()`
- `SearchPlanBuilder.build_for_query_type(query_type)`
- `SearchPlanBuilder.validate(search_plan)`

## Inputs

- User query text, indirectly through retrieval and agent routing.
- Query type, when using `build_for_query_type(query_type)`.
- Optional explicit `SearchPlan` supplied by tool, CLI, agent, or future MCP caller.

## Outputs

- A validated `SearchPlan` object or validation error.

## Side effects

None. Search planning is configuration construction and validation only.

## Testing requirements

Test supported fields, unsupported values, defaults, query-type mappings, top-k limits, search layer validation, score mode validation, and reranker configuration.

## What this must not do

- Execute search.
- Query Neo4j.
- Read or write documents.
- Call embeddings, rerankers, or LLMs.
- Contain business logic beyond selecting and validating configuration.

## Extension points

- Additional query types.
- Additional search layers.
- Additional score modes.
- Additional reranker modes.
- Optional query classification integration.
