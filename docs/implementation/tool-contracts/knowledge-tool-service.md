# Knowledge Tool Service

## Purpose

This file defines the shared request/response contracts and the `KnowledgeToolService` facade used by LangChain StructuredTools, CLI commands, and future MCP adapters.

## When to read this

Read this when changing:

- tool-facing Pydantic request models;
- tool-facing Pydantic response models;
- facade methods;
- validation/delegation behavior;
- CLI, StructuredTool, or MCP calls into core services.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [search-plan.md](search-plan.md)
- [retrieval-tools.md](retrieval-tools.md)
- [qa-tools.md](qa-tools.md)
- [future-mcp-adapter.md](future-mcp-adapter.md)

## Source of truth

This file is authoritative for `KnowledgeToolService`, `SearchDocumentsRequest`, `SearchDocumentsResponse`, `AnswerQuestionRequest`, and `AnswerQuestionResponse`.

## Content

### Request and response contracts

#### `SearchDocumentsRequest`

Represents input for document search.

```python
class SearchDocumentsRequest(BaseModel):
    query: str
    search_plan: SearchPlan | None = None
```

| Field | Purpose |
|---|---|
| `query` | Natural-language or keyword query from user/agent |
| `search_plan` | Optional explicit strategy; default is created when omitted |

Used by:

```text
KnowledgeToolService.search_documents
RetrievalService.search_documents
LangChain StructuredTool: search_documents
Future MCP tool: search_documents
CLI command: kb search
```

#### `SearchDocumentsResponse`

Represents ranked search results.

Must include:

```text
query
search_plan_used
results
warnings
latency metadata if available
```

Each result should include:

```text
document_id
title
file_path
document_type
summary
tags
entities
created_at
modified_at
confidence
score_breakdown
matched_chunks
related_documents
source_refs
```

Used by:

```text
LangGraph agent
CLI renderer
future MCP server
future API/UI
benchmark evaluation
```

#### `AnswerQuestionRequest`

Represents input for source-grounded Q&A.

```python
class AnswerQuestionRequest(BaseModel):
    question: str
    search_plan: SearchPlan | None = None
    document_ids: list[str] | None = None
    include_supporting_text: bool = True
    top_k_chunks: int = 8
```

| Field | Purpose |
|---|---|
| `question` | User question |
| `search_plan` | Optional retrieval strategy |
| `document_ids` | Optional constraint to specific documents |
| `include_supporting_text` | Whether to return chunk text in response |
| `top_k_chunks` | Maximum supporting chunks used for answer |

Used by:

```text
KnowledgeToolService.answer_question
QAService.answer_question
LangChain StructuredTool: answer_question
Future MCP tool: answer_question
CLI command: kb ask
```

#### `AnswerQuestionResponse`

Represents a source-grounded answer.

Must include:

```text
question
answer
confidence
source_documents
supporting_chunks
missing_information
warnings
```

For document-text Q&A, `supporting_chunks.text` should be returned.

For document lookup questions, matched chunk summaries and source references are usually enough.

### `KnowledgeToolService`

`KnowledgeToolService` is the main facade used by LangChain tools, CLI commands, and future MCP adapters.

It exists to prevent adapters from calling low-level services directly.

#### Dependencies

```text
RetrievalService
QAService
GraphService
DocumentService
```

#### Methods

##### `search_documents(request)`

Purpose: validate and delegate document search.

Calls:

```text
RetrievalService.search_documents
```

Used by:

```text
StructuredTool search_documents
CLI kb search
Future MCP search_documents
```

##### `answer_question(request)`

Purpose: validate and delegate source-grounded Q&A.

Calls:

```text
QAService.answer_question
```

Used by:

```text
StructuredTool answer_question
CLI kb ask
Future MCP answer_question
```

##### `show_related_documents(request)`

Purpose: return graph-neighbor documents for one document.

Calls:

```text
GraphService.get_related_documents
DocumentService.enrich_document_cards
```

Used by:

```text
StructuredTool show_related_documents
CLI kb related
Future MCP show_related_documents
```

##### `get_document_summary(request)`

Purpose: retrieve document metadata, summary, tags, and entities.

Calls:

```text
DocumentService.get_document_summary
```

Used by:

```text
StructuredTool get_document_summary
Future MCP get_document_summary
```

##### `get_document_chunks(request)`

Purpose: retrieve chunk text/summaries/source refs for a document.

Calls:

```text
DocumentService.get_document_chunks
```

Used by:

```text
StructuredTool get_document_chunks
QAService constrained document Q&A
Future MCP get_document_chunks
```

##### `find_duplicates(request)`

Purpose: inspect exact duplicate relationships.

Calls:

```text
DocumentService.find_duplicates
GraphService.get_duplicate_edges
```

Used by:

```text
StructuredTool find_duplicates
CLI kb duplicates
Future MCP find_duplicates
```

##### `explain_document_relationship(request)`

Purpose: explain relationship evidence between two documents.

Calls:

```text
GraphService.get_relationship_evidence
DocumentService.get_document_summary
```

Used by:

```text
StructuredTool explain_document_relationship
Future graph UI
Future MCP explain_document_relationship
```

## Dependencies

- `RetrievalService`
- `QAService`
- `GraphService`
- `DocumentService`
- Pydantic request and response schemas
- `SearchPlan`

## Failure modes / risks

- Adapters bypass `KnowledgeToolService` and call low-level services directly.
- Facade methods start containing business logic instead of validation and delegation.
- Request/response contracts diverge between CLI, StructuredTools, and future MCP.
- `SearchPlan` validation is skipped before retrieval.

## Validation

Verify:

- `KnowledgeToolService` validates request models before delegation.
- `KnowledgeToolService.search_documents` calls `RetrievalService.search_documents`.
- `KnowledgeToolService.answer_question` calls `QAService.answer_question`.
- document-inspection facade methods call `DocumentService` and/or `GraphService` as specified.
- outputs remain Pydantic models serializable to JSON.

## Update rules

Update this file when shared request/response fields, facade dependencies, facade methods, delegation targets, validation behavior, or adapter-facing contracts change.

## Public API / Methods

- `KnowledgeToolService.search_documents(request)`
- `KnowledgeToolService.answer_question(request)`
- `KnowledgeToolService.show_related_documents(request)`
- `KnowledgeToolService.get_document_summary(request)`
- `KnowledgeToolService.get_document_chunks(request)`
- `KnowledgeToolService.find_duplicates(request)`
- `KnowledgeToolService.explain_document_relationship(request)`

## Inputs

- `SearchDocumentsRequest`
- `AnswerQuestionRequest`
- `RelatedDocumentsRequest`
- `DocumentSummaryRequest`
- `DocumentChunksRequest`
- `FindDuplicatesRequest`
- `ExplainDocumentRelationshipRequest`

Only `SearchDocumentsRequest` and `AnswerQuestionRequest` are fully defined in the source contract. Other request names and typical fields are defined in [retrieval-tools.md](retrieval-tools.md).

## Outputs

- `SearchDocumentsResponse`
- `AnswerQuestionResponse`
- `RelatedDocumentsResponse`
- `DocumentSummaryResponse`
- `DocumentChunksResponse`
- `FindDuplicatesResponse`
- `ExplainDocumentRelationshipResponse`

Only `SearchDocumentsResponse` and `AnswerQuestionResponse` are fully defined in the source contract. Other response names are public contract names from the tool signatures.

## Side effects

None in MVP. The facade routes read-only tool calls to core services.

## Testing requirements

Test facade validation, delegation target, no direct graph/storage/model logic inside facade methods, and JSON-serializable output shapes.

## What this must not do

- Implement retrieval pipelines.
- Implement Q&A pipelines.
- Query Neo4j directly.
- Read processed JSON directly except through owned services.
- Call LLMs, embeddings, or rerankers directly.
- Expose ingestion or destructive actions in MVP.

## Extension points

- Future MCP adapter calls into the same facade methods.
- Future API/UI adapters call into the same facade methods.
- Additional read-only tool methods can be added when they preserve the facade boundary.
