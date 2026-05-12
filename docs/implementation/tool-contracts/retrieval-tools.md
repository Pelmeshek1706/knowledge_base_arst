# Retrieval Tools

## Purpose

This file defines read-only retrieval and document-inspection tool behavior, including search, related documents, summaries, chunks, duplicate inspection, and relationship explanation.

## When to read this

Read this when changing:

- `search_documents`;
- related-document lookup;
- document summaries;
- document chunk lookup;
- duplicate inspection;
- relationship evidence explanations;
- `RetrievalService`;
- `GraphService` methods used by tools;
- `DocumentService` read-only methods.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [search-plan.md](search-plan.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [qa-tools.md](qa-tools.md)
- [langchain-structured-tools.md](langchain-structured-tools.md)
- [future-mcp-adapter.md](future-mcp-adapter.md)

## Source of truth

This file is authoritative for retrieval and document-inspection tool behavior and for the backing `RetrievalService`, `GraphService`, and `DocumentService` methods used by those tools.

## Content

## Public API / Methods

### `search_documents`

#### Purpose

Find documents relevant to a user query.

This is the main tool for questions like:

```text
Where is information about X?
Which documents are related to accounting and budgets?
Find documents mentioning Penelope.
Where was WP2 discussed?
```

#### Layer ownership

| Layer | Responsibility |
|---|---|
| LangChain StructuredTool | validates tool input and calls `KnowledgeToolService` |
| KnowledgeToolService | facade method, validates request, delegates to `RetrievalService` |
| RetrievalService | executes search layers and candidate ranking |
| GraphService | graph, tag, entity, keyword, vector queries |
| EmbeddingClient | embeds query for vector search |
| RerankerClient | reranks candidates when enabled |
| ScoringService | computes hybrid score |

#### Function signature

```python
def search_documents(request: SearchDocumentsRequest) -> SearchDocumentsResponse:
    ...
```

StructuredTool wrapper signature:

```python
def search_documents(query: str, search_plan: dict | None = None) -> dict:
    ...
```

#### Dependencies

```text
RetrievalService
GraphService
EmbeddingClient
RerankerClient
ScoringService
ProcessedDocumentStore only if extra document metadata is needed
```

#### Side effects

None. This tool is read-only.

#### Output

Returns ranked document cards with confidence scores, score breakdown, summaries, tags, matched chunks, related documents, and source references.

#### Errors

| Error | Meaning | Recommended handling |
|---|---|---|
| `InvalidSearchPlanError` | `SearchPlan` is malformed | return validation error |
| `Neo4jUnavailableError` | graph backend unavailable | return tool error with retry hint |
| `EmbeddingUnavailableError` | vector search unavailable | fallback to keyword/entity/tag if allowed |
| `RerankerUnavailableError` | reranker unavailable | fallback to hybrid formula without reranker |

#### Used by

```text
LangGraph QueryRouterNode
CLI: kb search
Future MCP: search_documents
Future API: /search
Benchmark retrieval evaluation
```

### `show_related_documents`

#### Purpose

Return documents related to a given document through graph relationships.

This tool answers:

```text
What documents are related to this document?
What else is connected to this report?
Show documents connected to this budget file.
```

#### Function signature

```python
def show_related_documents(request: RelatedDocumentsRequest) -> RelatedDocumentsResponse:
    ...
```

Typical request fields:

```text
document_id
relationship_types
max_depth
top_k
include_reason
```

#### Dependencies

```text
GraphService
DocumentService
ScoringService optional
```

#### Relationship evidence

For MVP, relatedness is deterministic and can come from:

```text
DUPLICATE_OF
NEWER_VERSION_OF
RELATED_TO
shared tags
shared entities
same DocumentType
high vector similarity if precomputed or queried
```

No LLM-inferred relationship generation in MVP.

#### Side effects

None.

#### Used by

```text
LangGraph relationship route
CLI: kb related
Future MCP: show_related_documents
Future UI graph/document browser
```

### `get_document_summary`

#### Purpose

Return document-level metadata, summary, tags, entities, duplicate/version status, and source references.

This tool answers:

```text
What is this document about?
Show summary for doc_id.
What tags/entities does this document have?
```

#### Function signature

```python
def get_document_summary(request: DocumentSummaryRequest) -> DocumentSummaryResponse:
    ...
```

Typical request fields:

```text
document_id or file_path
include_entities
include_tags
include_relationships
```

#### Dependencies

```text
DocumentService
ProcessedDocumentStore
GraphService optional for relationship metadata
```

#### Side effects

None.

#### Used by

```text
LangGraph document inspection route
CLI future command: kb doc summary
Future MCP: get_document_summary
Future UI document details panel
```

### `get_document_chunks`

#### Purpose

Return chunks for a document.

This tool is used when the agent needs source text for precise Q&A or when a user asks about a specific section/page/sheet.

#### Function signature

```python
def get_document_chunks(request: DocumentChunksRequest) -> DocumentChunksResponse:
    ...
```

Typical request fields:

```text
document_id
page
section
sheet
cell_range
include_text
top_k
```

#### Dependencies

```text
DocumentService
ProcessedDocumentStore
GraphService optional
```

#### Side effects

None.

#### Used by

```text
QAService when constrained to a specific document
LangGraph follow-up tool call
Future MCP: get_document_chunks
Debugging and document inspection
```

### `find_duplicates`

#### Purpose

Find exact duplicates using raw bytes hash and/or extracted text hash.

This tool answers:

```text
Are there duplicate documents?
Is this document duplicated somewhere else?
```

#### Function signature

```python
def find_duplicates(request: FindDuplicatesRequest) -> FindDuplicatesResponse:
    ...
```

Typical request fields:

```text
document_id optional
file_path optional
scope: one_document | all
hash_type: raw_bytes | extracted_text | both
```

#### Dependencies

```text
DocumentService
ProcessedDocumentStore
GraphService
```

#### Side effects

None.

Important: The tool only reports duplicates. It does not delete, merge, move, or rename files.

#### Used by

```text
CLI: kb duplicates
LangGraph duplicate inspection route
Future MCP: find_duplicates
```

### `explain_document_relationship`

#### Purpose

Explain why two documents are connected.

This tool answers:

```text
Why are document A and document B related?
How is this budget file connected to that report?
Is this a duplicate or newer version?
```

#### Function signature

```python
def explain_document_relationship(
    request: ExplainDocumentRelationshipRequest,
) -> ExplainDocumentRelationshipResponse:
    ...
```

Typical request fields:

```text
source_document_id
target_document_id
include_evidence_chunks
max_evidence_items
```

#### Dependencies

```text
GraphService
DocumentService
ProcessedDocumentStore
```

Optional later:

```text
LLMClient for natural-language explanation polishing
```

#### MVP behavior

Explanation must be deterministic and evidence-based.

Supported evidence:

```text
direct relationship edge
shared tags
shared entities
same document type
version relation
exact duplicate relation
matched chunks or source refs
```

#### Side effects

None.

#### Used by

```text
LangGraph relationship route
CLI future command: kb explain-relation
Future MCP: explain_document_relationship
Future UI graph edge explanation
```

### `RetrievalService`

`RetrievalService` owns search behavior.

It converts a query and `SearchPlan` into ranked document results.

#### Dependencies

```text
GraphService
EmbeddingClient
RerankerClient
ScoringService
CandidateMerger
SearchPlanBuilder
```

#### Methods

##### `search_documents(request)`

Purpose: top-level retrieval pipeline.

Steps:

```text
1. Build default SearchPlan if none is provided.
2. Validate SearchPlan.
3. Run enabled search layers.
4. Merge candidates.
5. Compute hybrid scores.
6. Apply reranker if enabled.
7. Attach matched chunks and related documents.
8. Return SearchDocumentsResponse.
```

Used by:

```text
KnowledgeToolService.search_documents
QAService.retrieve_context
Benchmark retrieval evaluation
```

##### `run_keyword_search(query, filters)`

Purpose: find exact or near-exact matches in title, path, document type, tags, and normalized text fields.

Calls:

```text
GraphService.search_keyword
```

Used by:

```text
search_documents when keyword layer is enabled
```

##### `run_entity_search(query, filters)`

Purpose: match query terms to extracted entities and documents mentioning them.

Calls:

```text
GraphService.search_entities
GraphService.get_documents_by_entities
```

Used by:

```text
search_documents when entity layer is enabled
```

##### `run_tag_search(query, filters)`

Purpose: match query terms to normalized tags and related documents.

Calls:

```text
GraphService.search_tags
GraphService.get_documents_by_tags
```

Used by:

```text
search_documents when tag layer is enabled
```

##### `run_vector_search(query, filters, top_k)`

Purpose: semantic search over chunk embeddings.

Calls:

```text
EmbeddingClient.embed_query
GraphService.vector_search_chunks
```

Used by:

```text
search_documents when vector layer is enabled
QAService.retrieve_context
```

##### `run_graph_expansion(candidates, search_plan)`

Purpose: expand candidate documents through graph relationships.

Calls:

```text
GraphService.expand_documents
GraphService.get_related_documents
```

Used by:

```text
search_documents when graph layer is enabled
```

##### `rerank_candidates(query, candidates, search_plan)`

Purpose: reorder candidates using local reranker after candidate pruning.

Calls:

```text
RerankerClient.rerank
```

Used by:

```text
search_documents when reranker is enabled
```

### `GraphService`

`GraphService` owns Neo4j queries and graph traversal.

#### Dependencies

```text
Neo4jClient
GraphRepository
Config
```

#### Methods

##### `setup_schema()`

Purpose: create constraints, indexes, and vector indexes.

Used by:

```text
CLI kb setup-db
Optional kb ingest --auto-setup-db
```

Not used by:

```text
LangGraph agent
StructuredTools
MCP tools in MVP
```

##### `search_keyword(query, filters)`

Purpose: search document titles, paths, tags, and optionally chunk text by keyword.

Used by:

```text
RetrievalService.run_keyword_search
```

##### `search_entities(query, filters)`

Purpose: find matching `Entity` nodes.

Used by:

```text
RetrievalService.run_entity_search
```

##### `search_tags(query, filters)`

Purpose: find matching `Tag` nodes.

Used by:

```text
RetrievalService.run_tag_search
```

##### `vector_search_chunks(query_embedding, top_k, filters)`

Purpose: run Neo4j vector index search over `Chunk.embedding`.

Used by:

```text
RetrievalService.run_vector_search
QAService.retrieve_context
```

##### `get_related_documents(document_id, relationship_types, max_depth, top_k)`

Purpose: return documents connected through deterministic relationships.

Used by:

```text
KnowledgeToolService.show_related_documents
RetrievalService.run_graph_expansion
```

##### `get_relationship_evidence(source_document_id, target_document_id)`

Purpose: explain graph evidence between two documents.

Used by:

```text
KnowledgeToolService.explain_document_relationship
```

##### `get_duplicate_edges(document_id=None)`

Purpose: retrieve `DUPLICATE_OF` relationships.

Used by:

```text
KnowledgeToolService.find_duplicates
DocumentService.find_duplicates
```

### `DocumentService`

`DocumentService` owns read-only document inspection.

#### Dependencies

```text
ProcessedDocumentStore
GraphService optional
```

#### Methods

##### `get_document_summary(document_id_or_path)`

Purpose: return document-level summary and metadata.

Used by:

```text
KnowledgeToolService.get_document_summary
QAService citation/context enrichment
CLI/UI document view
```

##### `get_document_chunks(request)`

Purpose: return chunks filtered by page, section, sheet, cell range, or top-k.

Used by:

```text
KnowledgeToolService.get_document_chunks
QAService.retrieve_context
```

##### `find_duplicates(request)`

Purpose: inspect duplicates using hash fields and/or graph relationships.

Used by:

```text
KnowledgeToolService.find_duplicates
CLI kb duplicates
```

##### `enrich_document_cards(document_ids)`

Purpose: attach summary, tags, source refs, and metadata to candidate document IDs.

Used by:

```text
RetrievalService final response assembly
GraphService related document results
```

## Dependencies

- `KnowledgeToolService`
- `RetrievalService`
- `GraphService`
- `DocumentService`
- `SearchPlan`
- `SearchPlanBuilder`
- `EmbeddingClient`
- `RerankerClient`
- `ScoringService`
- `CandidateMerger`
- `ProcessedDocumentStore`
- `Neo4jClient`
- `GraphRepository`
- `Config`

## Failure modes / risks

- `InvalidSearchPlanError`: `SearchPlan` is malformed.
- `Neo4jUnavailableError`: graph backend unavailable.
- `EmbeddingUnavailableError`: vector search unavailable; fallback to keyword/entity/tag if allowed.
- `RerankerUnavailableError`: reranker unavailable; fallback to hybrid formula without reranker.
- Duplicate tools accidentally mutate files instead of reporting duplicates.
- Relationship explanations use LLM-inferred relationships in MVP instead of deterministic evidence.
- `GraphService.setup_schema()` is exposed through agent tools, StructuredTools, or MCP tools in MVP.

## Validation

Verify:

- `search_documents` returns ranked document cards with confidence scores, score breakdown, summaries, tags, matched chunks, related documents, and source references.
- `show_related_documents` uses deterministic graph evidence.
- `get_document_summary` returns document-level metadata, summary, tags, entities, duplicate/version status, and source references.
- `get_document_chunks` supports page, section, sheet, cell range, `include_text`, and `top_k` request fields as implemented.
- `find_duplicates` reports duplicates without deletion, merge, move, or rename actions.
- `explain_document_relationship` is deterministic and evidence-based in MVP.
- `RetrievalService.search_documents` follows the documented eight-step pipeline.

## Update rules

Update this file when retrieval tool signatures, request fields, output fields, service dependencies, graph/document service methods, side effects, errors, or deterministic evidence rules change.

## Inputs

- `SearchDocumentsRequest`
- `RelatedDocumentsRequest`
- `DocumentSummaryRequest`
- `DocumentChunksRequest`
- `FindDuplicatesRequest`
- `ExplainDocumentRelationshipRequest`
- `SearchPlan`
- document IDs, file paths, relationship types, filters, and query text

## Outputs

- `SearchDocumentsResponse`
- `RelatedDocumentsResponse`
- `DocumentSummaryResponse`
- `DocumentChunksResponse`
- `FindDuplicatesResponse`
- `ExplainDocumentRelationshipResponse`

## Side effects

None in MVP. All tools in this file are read-only.

## Testing requirements

Unit tests must cover retrieval candidate merging, scoring formula, document chunk filtering, and graph query parameter construction.

Integration tests must cover:

```text
kb setup-db creates schema
search_documents returns expected document from Neo4j
find_duplicates returns DUPLICATE_OF relationship
show_related_documents returns graph neighbors
```

Contract tests must verify StructuredTool input/output schema compatibility for these tools.

## What this must not do

- Generate final answers.
- Trigger ingestion.
- Delete, merge, move, or rename files.
- Create LLM-inferred relationships in MVP.
- Expose graph schema setup through the LangGraph agent, StructuredTools, or MCP tools in MVP.
- Put Cypher, scoring, reranking, or manifest-reading logic inside tool wrappers.

## Extension points

- Optional LLM polishing for relationship explanations later.
- Future UI graph/document browser.
- Future MCP exposure of the same operations.
- Additional deterministic relationship evidence sources.
