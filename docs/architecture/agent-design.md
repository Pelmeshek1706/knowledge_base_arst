# Agent Design

## Purpose

This file defines the architecture for the internal LangGraph agent, LangChain `StructuredTool` wrappers, `KnowledgeToolService`, CLI command surface, future MCP adapter, and agent safety boundaries.

## When to read this

Read this file when changing LangGraph orchestration, StructuredTool exposure, `KnowledgeToolService`, tool-facing service methods, CLI commands, future MCP adapter behavior, agent-access policy, or controlled write-action rules.

## Related files

- [overview.md](overview.md)
- [retrieval-design.md](retrieval-design.md)
- [qa-design.md](qa-design.md)
- [graph-schema.md](graph-schema.md)
- [storage-design.md](storage-design.md)
- [model-strategy.md](model-strategy.md)

## Source of truth

This file is authoritative for MVP agent implementation, internal runtime path, core service boundary, allowed LangChain `StructuredTool` wrappers, LangGraph orchestration, operations not exposed to the agent, future MCP adapter plan, future agent tools, CLI architecture, CLI output policy, and controlled write-action rules.

## Content

### Responsibility

The agent/tool layer exposes search and Q&A capabilities to users while preserving core service boundaries and safety constraints.

The MVP uses an internal agent/tool path based on LangGraph and LangChain `StructuredTool` wrappers:

```text
User
-> LangGraph personal_kb agent
-> LangChain StructuredTools
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService
-> Neo4j + kb_storage + local models
```

This means:

- LangGraph is the internal orchestration layer for the MVP agent.
- Personal KB capabilities are exposed to LangGraph as LangChain `StructuredTool` objects.
- Every `StructuredTool` calls `KnowledgeToolService`.
- `KnowledgeToolService` calls core Python services directly.
- Business logic must not be implemented inside tools.
- MCP is not used as the primary internal execution path in MVP.

### Component boundaries

Core services are the real implementation layer:

```text
KnowledgeToolService
RetrievalService
QAService
GraphService
DocumentService
DuplicateService
RelationshipService
```

The same core service methods should be reusable from:

```text
CLI
LangChain StructuredTools
future MCP server adapter
future API / Telegram bot / web UI
```

Tools and adapters should not contain Neo4j queries, reranking logic, answer generation, file parsing, or other business logic.

### LangChain StructuredTools

LangChain `StructuredTool` wrappers are schema-bound adapters over core services.

Allowed MVP StructuredTools:

```text
search_documents
answer_question
show_related_documents
get_document_summary
get_document_chunks
find_duplicates
explain_document_relationship
```

Each StructuredTool must:

1. validate request arguments with Pydantic schemas;
2. call `KnowledgeToolService`;
3. return schema-valid structured JSON;
4. avoid Neo4j queries, reranking, answer generation, file parsing, or other business logic inside the wrapper.

### LangGraph orchestration

LangGraph should orchestrate query-time flow, not ingestion.

Minimum MVP flow:

```text
Input question
-> classify query intent
-> build or use default search_plan
-> call one or more StructuredTools
-> merge/validate tool outputs
-> return structured answer/search result
```

Possible nodes:

```text
InputNode
QueryRouterNode
SearchPlanNode
ToolExecutionNode
AnswerValidationNode
OutputNode
```

LangGraph may route between:

```text
document lookup
source-grounded Q&A
related-document lookup
duplicate inspection
relationship explanation
```

### Not exposed to agent in MVP

```text
rebuild_graph_from_manifest
ingest_documents
sync_neo4j_from_json
setup_db
delete_document
move_file
rename_file
send_email
update_confluence_page
create_jira_task
```

Rationale: ingestion, graph rebuild, schema setup, and graph sync are internal application/CLI operations, not agent decisions.

### MCP implementation plan

MCP is added after MVP core tools are stable.

Future MCP server adapter:

```text
External Agent / Client
-> MCP server adapter
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService
-> Neo4j + kb_storage + local models
```

MCP must expose the same core tools as the LangChain StructuredTool layer, not separate implementations.

Future MCP client integrations may be used for external sources:

```text
Confluence MCP client
Jira MCP client
Gmail MCP client
Google Drive / Docs / Sheets / Slides MCP clients
```

These future source connectors must normalize external objects into the same internal document contracts used by local files.

### Future agent tools

Later controlled write tools may be added:

```text
create_faq_entry
update_faq_entry
suggest_document_tags
suggest_document_links
create_confluence_page_draft
link_document_to_jira_issue
prepare_email_with_document_links
```

Destructive or external write actions must require confirmation:

```text
move_file
rename_file
delete_file
update_external_document
send_email
```

### CLI architecture

Initial CLI commands:

```bash
kb setup-db
kb ingest data
kb ingest data --auto-setup-db
kb search "accounting budget"
kb search "accounting budget" --json
kb ask "Where is information about WP2?"
kb related --doc-id <uuid>
kb duplicates
kb status
```

CLI responsibilities:

| Command | Responsibility |
|---|---|
| `kb setup-db` | create/check Neo4j constraints, indexes, vector index |
| `kb ingest` | deterministic ingestion pipeline and automatic Neo4j sync |
| `kb search` | document lookup |
| `kb ask` | source-grounded Q&A |
| `kb related` | graph relationship lookup |
| `kb duplicates` | duplicate inspection |
| `kb status` | manifest/Neo4j sync status |

CLI output policy:

Default output:

```text
human-readable
```

Optional output:

```bash
--json
```

Machine-readable output should follow the same tool contracts as MCP/agent tools.

### Future user interfaces

Future UI options:

```text
Telegram bot
local web app
React UI
Obsidian-like document explorer
Neo4j Bloom / graph visualization
VS Code extension
```

### Controlled write actions

Future write actions should be confirmation-based:

```text
create_confluence_page_draft
link_document_to_jira_issue
prepare_email_with_document_links
suggest_file_move
suggest_file_rename
```

Destructive actions require explicit confirmation.

## Public API / Methods

The source document defines service names and tool contracts but does not finalize method signatures.

Tool-facing capabilities:

- `search_documents`
- `answer_question`
- `show_related_documents`
- `get_document_summary`
- `get_document_chunks`
- `find_duplicates`
- `explain_document_relationship`

Core services:

- `KnowledgeToolService`
- `RetrievalService`
- `QAService`
- `GraphService`
- `DocumentService`
- `DuplicateService`
- `RelationshipService`

## Inputs

- user questions or CLI arguments
- Pydantic-validated tool request schemas
- optional search plans
- core service outputs
- processed JSON from [storage-design.md](storage-design.md)
- Neo4j graph data from [graph-schema.md](graph-schema.md)

## Outputs

- schema-valid structured JSON for tool calls
- human-readable CLI output by default
- machine-readable CLI output with `--json`
- structured answers/search results from core services

## Side effects

Allowed MVP side effects:

- CLI `kb setup-db` creates/checks Neo4j schema.
- CLI `kb ingest` runs deterministic ingestion and graph sync.
- CLI `kb status` reads manifest/Neo4j sync status.

Agent-side MVP tools should not mutate source files, run ingestion, rebuild the graph, set up the database, send emails, update Confluence, or create Jira tasks.

## Testing requirements

Validate agent/tool behavior by checking that:

- each StructuredTool validates arguments with Pydantic schemas;
- each StructuredTool calls `KnowledgeToolService`;
- wrappers contain no business logic;
- LangGraph routes document lookup, source-grounded Q&A, related-document lookup, duplicate inspection, and relationship explanation;
- non-agent operations remain CLI/internal only;
- machine-readable CLI output follows the same contracts as agent/MCP tools.

## What this must not do

- Do not expose ingestion, setup, sync, rebuild, delete, move, rename, email, Confluence update, or Jira creation actions to the MVP agent.
- Do not use MCP as the primary internal execution path in MVP.
- Do not implement separate MCP business logic later; MCP must adapt the same core services.
- Do not put Neo4j queries, reranking, answer generation, file parsing, or other business logic inside tool wrappers.
- Do not allow destructive or external write actions without explicit confirmation in future phases.

## Extension points

- future MCP server adapter
- future API
- Telegram bot
- web UI
- controlled write tools
- source connectors through MCP clients

## Dependencies

- LangGraph
- LangChain `StructuredTool`
- Pydantic schemas
- `KnowledgeToolService`
- core services listed in this file
- retrieval design from [retrieval-design.md](retrieval-design.md)
- Q&A design from [qa-design.md](qa-design.md)
- graph design from [graph-schema.md](graph-schema.md)
- storage design from [storage-design.md](storage-design.md)

## Failure modes / risks

| Risk | Mitigation |
|---|---|
| too many agent powers | agent has search tools only |
| business logic inside tools | tools call core Python services only |
| unsafe write behavior | destructive or external write actions require confirmation |
| MCP divergence | future MCP adapter exposes same core tools, not separate implementations |
| CLI/tool contract drift | `--json` output follows same contracts as MCP/agent tools |

## Validation

Validate agent design by checking that:

- the MVP runtime path is `User -> LangGraph personal_kb agent -> LangChain StructuredTools -> KnowledgeToolService -> core services`;
- the agent uses search/query tools only;
- `StructuredTool` wrappers are schema-bound adapters;
- `KnowledgeToolService` delegates to core services;
- LangGraph orchestrates query-time flow, not ingestion;
- disallowed MVP agent actions remain inaccessible;
- future MCP adapter boundaries reuse the same core service capabilities;
- CLI commands match the command list in this file.

## Update rules

Update this file when LangGraph flow, StructuredTool list, tool schemas, service boundaries, `KnowledgeToolService`, CLI commands, CLI output policy, MCP adapter boundaries, future agent tools, controlled write rules, or agent safety constraints change.
