# Search, Q&A, CLI, and Agent Requirements

## Purpose

This file defines the Product Requirements for search, Q&A, CLI output, internal LangGraph agent orchestration, LangChain StructuredTools, and the future MCP adapter boundary.

## When to read this

Read this when changing query behavior, output contracts, CLI commands, agent tool access, `KnowledgeToolService` use, LangChain StructuredTools, or MCP adapter constraints.

## Related files

- [Product requirements index](index.md)
- [Functional requirements](functional-requirements.md)
- [Data and graph requirements](data-and-graph-requirements.md)
- [Users and stories](users-and-stories.md)
- [Validation and acceptance](validation-and-acceptance.md)

## Source of truth

This file is authoritative for Product Requirements FR-063 through FR-102, search/scoring requirements, Q&A output requirements, and CLI requirements.

## Content

## Search

| ID | Requirement | Priority |
|---|---|---|
| FR-063 | Default search pipeline must support keyword/title, entity, vector, graph expansion, and reranking. | P0 |
| FR-064 | Search must support configurable `search_plan`. | P0 |
| FR-065 | Search must support graph-first mode through `search_plan.priority`. | P1 |
| FR-066 | Search must return confidence score and score breakdown. | P0 |
| FR-067 | Search must support hybrid scoring formula. | P0 |
| FR-068 | Search must support hybrid scoring with reranker. | P0 |
| FR-069 | Search must return matched entities, matched chunks, related documents, and source references. | P0 |

## Q&A

| ID | Requirement | Priority |
|---|---|---|
| FR-070 | Q&A must answer using retrieved chunks. | P0 |
| FR-071 | Q&A must return source documents and source references. | P0 |
| FR-072 | Q&A must return supporting chunk text for content questions. | P0 |
| FR-073 | Q&A must return warnings when confidence is low or information is missing. | P1 |
| FR-074 | Q&A must avoid unsupported claims beyond retrieved context. | P0 |

## CLI

| ID | Requirement | Priority |
|---|---|---|
| FR-075 | CLI must expose `kb setup-db`. | P0 |
| FR-076 | CLI must expose `kb ingest data`. | P0 |
| FR-077 | CLI must expose `kb search "query"`. | P0 |
| FR-078 | CLI must expose `kb ask "question"`. | P0 |
| FR-079 | CLI must expose `kb related --doc-id <uuid>`. | P1 |
| FR-080 | CLI must expose `kb duplicates`. | P1 |
| FR-081 | CLI must expose `kb status`. | P1 |
| FR-082 | CLI output must be readable by default. | P0 |
| FR-083 | CLI must support `--json` for machine-readable output. | P0 |

## Agent Tools and Internal Orchestration

| ID | Requirement | Priority |
|---|---|---|
| FR-084 | MVP must use LangGraph as the internal agent orchestration layer. | P0 |
| FR-085 | MVP must expose Personal KB capabilities as LangChain `StructuredTool` wrappers. | P0 |
| FR-086 | StructuredTools must call `KnowledgeToolService` directly. | P0 |
| FR-087 | Business logic must not be implemented inside tools. | P0 |
| FR-088 | `KnowledgeToolService` must delegate to core services such as `RetrievalService`, `QAService`, and `GraphService`. | P0 |
| FR-089 | Agent-facing tools must include `search_documents`. | P0 |
| FR-090 | Agent-facing tools must include `answer_question`. | P0 |
| FR-091 | Agent-facing tools may include `show_related_documents`. | P1 |
| FR-092 | Agent-facing tools may include `get_document_summary`. | P1 |
| FR-093 | Agent-facing tools may include `get_document_chunks`. | P1 |
| FR-094 | Agent-facing tools may include `find_duplicates`. | P1 |
| FR-095 | Agent-facing tools may include `explain_document_relationship`. | P1 |
| FR-096 | Agent must not access ingestion, rebuild, sync, setup-db, delete, move, rename, email, Confluence update, or Jira creation tools in MVP. | P0 |

## MCP Adapter Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-097 | MCP must not be the primary internal execution path for MVP. | P0 |
| FR-098 | MCP server adapter should be added after MVP core tools are stable. | P1 |
| FR-099 | MCP server adapter must expose the same core capabilities as LangChain StructuredTools. | P1 |
| FR-100 | MCP server tools must reuse `KnowledgeToolService` and the same Pydantic input/output schemas. | P1 |
| FR-101 | Future external sources may be consumed through MCP clients. | P2 |
| FR-102 | Future MCP clients for Confluence/Jira/Gmail/Drive must normalize external content into the same internal document contracts. | P2 |

## Search and Scoring Requirements

### Default Search Pipeline

```text
exact keyword/title search
→ entity search
→ vector search over chunks
→ graph expansion around matched chunks/entities
→ reranking
```

`search_plan.priority` may override this order, including graph-first search.

### Hybrid Scoring Formula

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

Weights must be configurable.

### Search Output Contract

Search output must include:

- query;
- search mode;
- document results;
- confidence;
- score breakdown;
- title;
- file path;
- document type;
- summary;
- tags;
- created/modified dates;
- matched entities;
- matched chunks;
- source references;
- related documents.

## Q&A Output Requirements

Q&A response must include:

```json
{
  "question": "...",
  "answer": "...",
  "confidence": 0.84,
  "source_documents": [],
  "supporting_chunks": [],
  "missing_information": [],
  "warnings": []
}
```

For content questions, `supporting_chunks.text` must be returned.

For document lookup questions, matched chunk summary + source reference is enough by default.

## CLI Requirements

### Commands

```bash
kb setup-db
kb ingest data
kb search "accounting budget"
kb ask "Where is information about WP2?"
kb related --doc-id <uuid>
kb duplicates
kb status
```

### Output Modes

Default:

```text
human-readable console output
```

Optional:

```bash
--json
```

which returns structured JSON.

## Public API / Methods

Named tool/service interfaces in this PRD area:

- `KnowledgeToolService`
- `RetrievalService`
- `QAService`
- `GraphService`
- `search_documents`
- `answer_question`
- `show_related_documents`
- `get_document_summary`
- `get_document_chunks`
- `find_duplicates`
- `explain_document_relationship`

## Inputs

- User query or question.
- Optional configurable `search_plan`.
- Neo4j graph and vector state.
- Processed JSON and chunk text.
- CLI arguments and optional `--json`.

## Outputs

- Ranked search results with confidence, score breakdown, matched chunks, related documents, and source references.
- Source-grounded Q&A responses with supporting chunks and warnings.
- Readable CLI output by default.
- Structured JSON output for CLI `--json` and tool calls.

## Side effects

- Search, Q&A, related-document, duplicate, summary, chunk, and relationship-explanation tools are read-only in MVP.
- The internal LangGraph agent calls LangChain StructuredTools.
- StructuredTools call `KnowledgeToolService` directly.

## Testing requirements

- Test default search pipeline ordering and configurable `search_plan.priority`.
- Test hybrid scoring and reranker scoring with configurable weights.
- Test search output includes all required fields.
- Test Q&A refuses unsupported claims beyond retrieved context.
- Test content questions return `supporting_chunks.text`.
- Test document lookup questions can return matched chunk summaries and source references by default.
- Test CLI readable output and `--json` output.
- Test StructuredTools are thin wrappers over `KnowledgeToolService`.
- Test MVP agent tools exclude ingestion, rebuild, sync, setup-db, delete, move, rename, email, Confluence update, and Jira creation tools.

## What this must not do

- Must not expose destructive or ingestion tools to the MVP agent.
- Must not implement business logic inside tool wrappers.
- Must not make MCP the primary internal execution path for MVP.
- Must not duplicate core service contracts in a future MCP adapter.
- Must not answer Q&A questions with unsupported claims beyond retrieved context.

## Extension points

- Graph-first search through `search_plan.priority`.
- Optional P1 tools: `show_related_documents`, `get_document_summary`, `get_document_chunks`, `find_duplicates`, and `explain_document_relationship`.
- Future MCP server adapter over `KnowledgeToolService`.
- Future MCP clients for Confluence/Jira/Gmail/Drive normalized into internal document contracts.

## Dependencies

- `KnowledgeToolService`
- `RetrievalService`
- `QAService`
- `GraphService`
- LangGraph
- LangChain `StructuredTool`
- Neo4j graph/vector state
- Processed JSON and chunk text

## Failure modes / risks

- Low-confidence or missing information must produce Q&A warnings.
- Unsupported claims beyond retrieved context are not allowed.
- Too much agent autonomy is unsafe; the agent has search-only tools in MVP.
- Business logic inside tools makes behavior hard to test and duplicate across CLI/MCP/LangGraph.
- Premature MCP integration adds architecture complexity before core tools are stable.
- Search latency above ~10 seconds harms usability.

## Validation

- Verify FR-063 through FR-102 are covered by implementation, tests, or explicit backlog items.
- Verify search/Q&A outputs are schema-valid JSON for tool and `--json` use.
- Verify CLI commands match the documented command list.
- Verify the LangGraph → LangChain StructuredTools → KnowledgeToolService → core services route is preserved.

## Update rules

- Update this file when search, Q&A, CLI, agent tool, StructuredTool, `KnowledgeToolService`, or MCP adapter requirements change.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when query or output-contract changes affect benchmarks or acceptance criteria.
- Update [data-and-graph-requirements.md](data-and-graph-requirements.md) when search changes require different graph or storage data.
