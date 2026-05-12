# Tool Contracts Overview

## Purpose

This file explains the cross-cutting tool architecture for `personal_kb`: the MVP execution path, design rules, directory responsibilities, runtime flow, error model, testing requirements, documentation standard, and tool exposure summary.

## When to read this

Read this before changing:

- the tool/service layering model;
- runtime dependency flow;
- package responsibilities;
- global tool error handling;
- tool testing strategy;
- public tool documentation standards;
- MVP exposure rules.

## Related files

- [index.md](index.md)
- [search-plan.md](search-plan.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [retrieval-tools.md](retrieval-tools.md)
- [qa-tools.md](qa-tools.md)
- [langchain-structured-tools.md](langchain-structured-tools.md)
- [future-mcp-adapter.md](future-mcp-adapter.md)
- [../index.md](../index.md)
- [../../architecture/index.md](../../architecture/index.md)

## Source of truth

This file is authoritative for cross-cutting tool architecture, global design rules, runtime paths, error model, testing expectations, and MVP tool exposure. Focused files are authoritative for their specific contracts.

## Content

### Document status

```text
Status: Draft v0.3
Project: personal_kb
Python: 3.11
Package manager: uv
CLI framework: argparse
Primary MVP agent path: LangGraph -> LangChain StructuredTools -> KnowledgeToolService -> core services
MCP status: Post-MVP adapter over the same core tool contracts
Primary language of the source document: English
Last updated: 2026-05-09
```

### Implementation contract purpose

The tool contract documentation defines the tool contracts, directory responsibilities, function responsibilities, dependencies, and runtime usage for the `personal_kb` project.

It is intended for engineers who need to understand:

1. How the MVP agent calls tools.
2. What each tool does and does not do.
3. Which service owns each piece of business logic.
4. Which directory contains each implementation layer.
5. Which functions are public contracts versus internal helpers.
6. How future MCP support should reuse the same contracts without rewriting the core system.

This is not user-facing product documentation. It is an implementation-facing engineering contract.

### Final MVP decision

The MVP agent uses LangGraph internally and exposes `personal_kb` capabilities as LangChain StructuredTools.

```text
User
-> LangGraph personal_kb agent
-> LangChain StructuredTools
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService / DocumentService
-> Neo4j + kb_storage + local models
```

MCP is not the primary internal execution path in MVP.

MCP will be added later as an adapter:

```text
External MCP Client
-> personal_kb MCP Server Adapter
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService / DocumentService
-> Neo4j + kb_storage + local models
```

Future external sources may also be consumed through MCP clients:

```text
personal_kb Source Connector
-> MCP Client
-> Confluence / Jira / Gmail / Google Drive MCP Server
-> RawDocument contract
-> deterministic ingestion pipeline
```

This external source ingestion path is not MVP scope.

### Core design rules

#### Tools are adapters, not business logic containers

A tool must not contain Cypher queries, reranking logic, answer generation logic, graph traversal rules, or manifest-reading logic.

Bad:

```python
@tool
def search_documents(query: str) -> dict:
    # Neo4j query logic here
    # scoring logic here
    # reranker logic here
    # output formatting here
    ...
```

Correct:

```python
@tool
def search_documents(query: str, search_plan: dict | None = None) -> dict:
    request = SearchDocumentsRequest(query=query, search_plan=search_plan)
    response = knowledge_tool_service.search_documents(request)
    return response.model_dump()
```

#### Core services must be framework-independent

Core services must not import or depend on:

```text
LangGraph
LangChain StructuredTool
MCP SDK
argparse
FastAPI
Telegram bot SDK
UI code
```

Core services may depend on:

```text
Pydantic schemas
Neo4j repositories
Processed JSON storage
Local model clients
Config objects
Pure Python utilities
```

#### Ingestion is not agent-controlled in MVP

The agent may answer questions, search documents, inspect summaries, inspect chunks, inspect duplicate/version relationships, and explain graph relationships.

The agent must not trigger:

```text
ingest_documents
rebuild_graph_from_manifest
sync_neo4j_from_json
delete_document
move_file
rename_file
send_email
update_confluence_page
create_jira_task
```

These operations are internal CLI/system operations, not agent tools.

#### Every tool must return structured output

Each tool returns a Pydantic response model that can be serialized to JSON.

Human-readable rendering is the responsibility of:

```text
CLI renderer
future UI renderer
future Telegram bot adapter
future API layer
```

### Directory and module responsibilities

Recommended package layout:

```text
personal_kb/
  __init__.py

  schemas/
    __init__.py
    common.py
    search.py
    tools.py
    document.py
    chunk.py
    entity.py
    tag.py
    graph.py
    qa.py
    errors.py
    config.py

  core/
    __init__.py
    config_loader.py
    paths.py
    hashing.py
    normalization.py
    ids.py
    logging.py

  storage/
    __init__.py
    manifest_store.py
    processed_document_store.py

  graph/
    __init__.py
    neo4j_client.py
    graph_repository.py
    graph_schema_manager.py
    graph_sync_service.py

  retrieval/
    __init__.py
    retrieval_service.py
    search_plan_builder.py
    scoring_service.py
    rerank_service.py
    candidate_merger.py

  qa/
    __init__.py
    qa_service.py
    answer_prompt_builder.py
    citation_builder.py

  documents/
    __init__.py
    document_service.py
    chunk_service.py

  models/
    __init__.py
    llm_client.py
    embedding_client.py
    reranker_client.py

  tools/
    __init__.py
    knowledge_tool_service.py
    structured_tools.py
    tool_registry.py

  agents/
    __init__.py
    langgraph_agent.py
    state.py
    nodes.py
    routing.py

  adapters/
    __init__.py
    cli/
      __init__.py
      main.py
      renderers.py
    mcp/
      __init__.py
      server.py
      converters.py

  tests/
    unit/
    integration/
    fixtures/
```

#### `schemas/`

Contains Pydantic models shared across services, tools, CLI, and future MCP adapters.

Rules:

- No Neo4j driver imports.
- No LangGraph imports.
- No LangChain imports.
- No MCP SDK imports.
- Only data structures, enums, validation logic, and serialization helpers.

#### `core/`

Contains pure utilities and project-wide infrastructure helpers.

Examples:

- path resolution
- hash computation
- ID generation
- config loading
- normalization
- structured logging setup

Rules:

- No business workflows.
- No tool definitions.
- No direct user interaction.

#### `storage/`

Owns local JSON state.

Responsibilities:

- read/write `kb_storage/manifest.json`
- read/write `kb_storage/documents/<document_id>.json`
- preserve failed document records
- provide processed document data to graph sync and document lookup services

Rules:

- Does not call LLMs.
- Does not call embeddings.
- Does not query Neo4j.
- Does not decide search logic.

#### `graph/`

Owns Neo4j access and graph schema operations.

Responsibilities:

- connect to Neo4j
- create constraints and indexes
- create vector index
- upsert documents/chunks/entities/tags/document types
- query graph relationships
- execute vector search through Neo4j

Rules:

- No LangGraph or LangChain tool code.
- Graph services should expose methods that other services can call.
- Cypher should be concentrated here, not spread across tools.

#### `retrieval/`

Owns search orchestration and retrieval logic.

Responsibilities:

- interpret `SearchPlan`
- run keyword/entity/tag/vector/graph search layers
- merge candidates
- apply scoring formula
- call reranker when enabled
- return ranked document/chunk candidates

Rules:

- Does not generate final answers.
- Does not modify documents.
- Does not write graph schema.

#### `qa/`

Owns source-grounded answer generation.

Responsibilities:

- call retrieval for supporting documents/chunks
- build context for the LLM
- call local LLM through model client
- return answer with citations, confidence, warnings, and missing information

Rules:

- Must answer from retrieved context.
- Must return sources.
- Must not invent unsupported facts.

#### `documents/`

Owns document-level read operations.

Responsibilities:

- get document summary
- get document chunks
- inspect document metadata
- inspect duplicate/version relations

Rules:

- Read-only in MVP.
- No ingestion trigger.
- No source file mutation.

#### `models/`

Owns model execution clients.

Responsibilities:

- call LM Studio OpenAI-compatible endpoint
- run local Qwen embedding model through `transformers` or `sentence-transformers`
- run local Qwen reranker model

Rules:

- No retrieval logic.
- No graph queries.
- No tool definitions.

#### `tools/`

Owns the stable tool-facing facade and LangChain StructuredTool wrappers.

Responsibilities:

- expose `KnowledgeToolService`
- define tool registry
- convert core service methods into LangChain StructuredTools

Rules:

- No business logic inside wrappers.
- Tools call service methods only.

#### `agents/`

Owns the LangGraph MVP agent.

Responsibilities:

- route user query type
- build or select `SearchPlan`
- execute StructuredTools
- merge tool outputs if needed
- return final structured agent response

Rules:

- Agent orchestrates.
- Services execute business logic.
- Tools provide controlled execution boundaries.

#### `adapters/cli/`

Owns CLI entrypoints and CLI rendering.

Responsibilities:

- `kb setup-db`
- `kb ingest`
- `kb search`
- `kb ask`
- `kb related`
- `kb duplicates`
- `kb status`

Rules:

- CLI calls services.
- CLI should support human-readable output by default and `--json` output when requested.

#### `adapters/mcp/`

Future adapter for MCP clients.

Responsibilities:

- expose the same core tools to external MCP clients
- convert MCP request payloads into Pydantic request models
- call `KnowledgeToolService`
- return serializable responses

Rules:

- Not primary path in MVP.
- Must reuse the same contracts as StructuredTools.
- Must not create a second implementation of retrieval/QA logic.

### Runtime dependency flow

#### MVP agent path

```text
User message
-> LangGraphPersonalKBAgent.invoke(...)
-> QueryRouterNode
-> SearchPlanBuilder
-> LangChain StructuredTool
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService / DocumentService
-> Neo4j / kb_storage / local models
-> structured response
```

#### Direct CLI path

```text
kb search "budget accounting"
-> argparse command handler
-> KnowledgeToolService.search_documents(...)
-> RetrievalService
-> GraphService + EmbeddingClient + RerankerClient
-> structured response
-> CLI renderer
```

#### Future MCP path

```text
External MCP client
-> personal_kb MCP server tool call
-> MCP adapter converter
-> KnowledgeToolService
-> same core services
-> structured response
```

### Error model

All service/tool errors should be represented in a structured way.

Recommended response fields:

```text
success: bool
error_code: string | null
error_message: string | null
warnings: list[str]
```

Common error codes:

| Error code | Meaning |
|---|---|
| `INVALID_INPUT` | Request schema validation failed |
| `INVALID_SEARCH_PLAN` | `SearchPlan` contains unsupported values |
| `NEO4J_UNAVAILABLE` | Neo4j connection failed |
| `MODEL_UNAVAILABLE` | LLM/embedding/reranker unavailable |
| `DOCUMENT_NOT_FOUND` | Document ID/path not found |
| `NO_RESULTS` | Search returned no candidates |
| `LOW_CONFIDENCE` | Result exists but confidence is low |
| `CITATION_ERROR` | Answer generated but citation mapping failed |

### Testing requirements

Unit tests must cover:

```text
SearchPlan validation
SearchPlanBuilder behavior
KnowledgeToolService delegation
StructuredTool wrapper calls
RetrievalService candidate merging
ScoringService formula
DocumentService chunk filtering
GraphService query parameter construction
```

Integration tests must cover:

```text
kb setup-db creates schema
search_documents returns expected document from Neo4j
answer_question returns answer with supporting chunks
find_duplicates returns DUPLICATE_OF relationship
show_related_documents returns graph neighbors
```

Contract tests must cover:

```text
StructuredTool input schema matches Pydantic request schema
StructuredTool output can serialize to JSON
Future MCP adapter returns same output shape as StructuredTool path
```

### Documentation standard for new functions

Every new public method or tool-facing function must document:

```text
Purpose
Layer ownership
Caller(s)
Dependencies
Input model
Output model
Side effects
Failure modes
Used by
Not responsible for
```

Template:

```markdown
### function_name

#### Purpose

#### Layer ownership

#### Called by

#### Dependencies

#### Input

#### Output

#### Side effects

#### Failure modes

#### Not responsible for
```

This rule exists because function names alone are not enough for maintainable project documentation.

### MVP tool exposure summary

| Tool | Exposed to LangGraph MVP agent | Exposed to MCP in MVP | Side effects | Core service |
|---|---:|---:|---:|---|
| `search_documents` | yes | no | none | `RetrievalService` |
| `answer_question` | yes | no | none | `QAService` |
| `show_related_documents` | yes | no | none | `GraphService` + `DocumentService` |
| `get_document_summary` | yes | no | none | `DocumentService` |
| `get_document_chunks` | yes | no | none | `DocumentService` |
| `find_duplicates` | yes | no | none | `DocumentService` + `GraphService` |
| `explain_document_relationship` | yes | no | none | `GraphService` |

MCP exposure is post-MVP and should reuse the same core contracts.

### Final recommendation

Implement in this order:

```text
1. Pydantic tool schemas
2. SearchPlan and SearchPlanBuilder
3. KnowledgeToolService facade
4. RetrievalService
5. QAService
6. DocumentService
7. GraphService methods needed by tools
8. LangChain StructuredTools
9. LangGraph agent nodes
10. CLI commands that reuse the same services
11. Future MCP adapter
```

The key design constraint is:

```text
Tools are transport/execution adapters.
Services own business logic.
Schemas define contracts.
LangGraph orchestrates.
MCP comes later as an external adapter.
```

## Dependencies

Cross-cutting tool architecture depends on:

- Pydantic schemas;
- `KnowledgeToolService`;
- `RetrievalService`;
- `QAService`;
- `GraphService`;
- `DocumentService`;
- Neo4j;
- `kb_storage`;
- local model clients;
- LangGraph and LangChain StructuredTools for the MVP agent path;
- future MCP adapter code after MVP.

## Failure modes / risks

- Tool wrappers accumulating business logic instead of delegating to services.
- Core services importing framework-specific packages such as LangGraph, LangChain, MCP SDKs, CLI adapters, or UI code.
- Agent-controlled ingestion or destructive operations being exposed in MVP.
- Unstructured tool outputs that cannot be serialized or rendered by downstream adapters.
- MCP being implemented as a second retrieval or Q&A pipeline instead of an adapter over `KnowledgeToolService`.

## Validation

Verify this layer by checking:

- tools call `KnowledgeToolService` instead of low-level services directly;
- core services do not import LangGraph, LangChain StructuredTool, MCP SDK, `argparse`, FastAPI, bot SDKs, or UI code;
- MVP agent tools are read-only;
- all public tools return Pydantic response models or serialized Pydantic output;
- unit, integration, and contract tests cover the requirements listed above.

## Update rules

Update this file when cross-cutting tool architecture, runtime flow, package responsibilities, error model, testing requirements, documentation standards, MVP exposure, or final implementation ordering changes. Update focused files for contract-specific changes.
