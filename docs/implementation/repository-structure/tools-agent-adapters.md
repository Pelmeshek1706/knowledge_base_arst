# Tools, Agent, And Adapters

## Purpose

This file defines the repository areas for the tool facade, LangChain `StructuredTool` wrappers, LangGraph agent orchestration, and framework-specific adapters.

## When to read this

Read this when implementing or changing `personal_kb/tools/`, `personal_kb/agent/`, or `personal_kb/adapters/`.

## Related files

- [graph-retrieval-qa.md](graph-retrieval-qa.md)
- [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md)
- [future-extensions.md](future-extensions.md)
- [../tool-contracts/index.md](../tool-contracts/index.md)
- [../class-design/tool-services.md](../class-design/tool-services.md)
- [../class-design/agent-services.md](../class-design/agent-services.md)
- [../../architecture/agent-design.md](../../architecture/agent-design.md)

## Source of truth

This file is authoritative for repository structure and responsibilities of tools, agent modules, and adapters. Tool method contracts are owned by the tool-contracts documentation.

## Content

## `personal_kb/tools/`

Purpose:

- expose stable tool API for agent and future MCP;
- no business logic inside wrappers.

### `knowledge_tool_service.py`

Facade over core services.

Methods:

```python
search_documents(request: SearchDocumentsRequest) -> SearchDocumentsResponse
answer_question(request: AnswerQuestionRequest) -> AnswerQuestionResponse
show_related_documents(request: RelatedDocumentsRequest) -> RelatedDocumentsResponse
get_document_summary(request: DocumentSummaryRequest) -> DocumentSummaryResponse
get_document_chunks(request: DocumentChunksRequest) -> DocumentChunksResponse
find_duplicates(request: FindDuplicatesRequest) -> FindDuplicatesResponse
explain_document_relationship(request: ExplainRelationshipRequest) -> ExplainRelationshipResponse
```

Used by:

- LangChain StructuredTools;
- LangGraph nodes;
- CLI search/ask commands;
- future MCP server adapter.

### `structured_tools.py`

Purpose:

- convert `KnowledgeToolService` methods into LangChain `StructuredTool` objects.

Rules:

- tools validate input using Pydantic schemas;
- tools call `KnowledgeToolService` only;
- tools do not query Neo4j directly;
- tools do not call local models directly.

### `tool_registry.py`

Purpose:

- list available MVP tools;
- build tool set for LangGraph agent;
- later build MCP-exposed tool list.

## `personal_kb/agent/`

Purpose:

- internal MVP agent orchestration using LangGraph.

### `state.py`

Defines LangGraph state:

```python
PersonalKBAgentState
```

Should include:

```text
user_query
query_type
search_plan
tool_results
answer
warnings
errors
```

### `graph.py`

Responsibilities:

- construct LangGraph workflow;
- wire nodes;
- attach StructuredTools;
- expose compiled agent.

### `nodes.py`

LangGraph nodes:

```text
InputNode
QueryRouterNode
SearchPlanNode
ToolExecutionNode
AnswerNode
OutputNode
```

Nodes must not contain business logic. They orchestrate service/tool calls only.

## `personal_kb/adapters/`

Purpose:

- framework-specific wrappers;
- no core business logic.

### `adapters/langchain/`

Purpose:

- LangChain StructuredTool integration.

### `adapters/langgraph/`

Purpose:

- LangGraph agent factory and runtime helpers.

### `adapters/mcp/`

Purpose:

- future MCP server adapter;
- not primary internal path in MVP.

Future responsibility:

```text
External MCP client
-> MCP server adapter
-> KnowledgeToolService
-> core services
```

Rules:

- expose the same core tools;
- do not duplicate tool logic;
- do not implement ingestion as MCP tool in MVP.

### `adapters/api/`

Reserved for future REST/FastAPI layer.

Not MVP.

## Dependencies

- `personal_kb/tools/knowledge_tool_service.py`
- `personal_kb/tools/structured_tools.py`
- `personal_kb/tools/tool_registry.py`
- `personal_kb/agent/state.py`
- `personal_kb/agent/graph.py`
- `personal_kb/agent/nodes.py`
- `personal_kb/adapters/langchain/`
- `personal_kb/adapters/langgraph/`
- `personal_kb/adapters/mcp/`
- `personal_kb/adapters/api/`

## Failure modes / risks

- Tool wrappers can accumulate business logic that belongs in `KnowledgeToolService` or lower services.
- Tools can bypass schemas and lose validation guarantees.
- LangGraph nodes can parse files, query Neo4j, or call models directly if boundaries are not enforced.
- MCP and API adapters can duplicate tool logic instead of adapting the same service facade.

## Validation

- Confirm tools validate inputs with Pydantic schemas.
- Confirm tools call `KnowledgeToolService` only.
- Confirm tools do not query Neo4j or call local models directly.
- Confirm LangGraph nodes orchestrate tool/service calls only.
- Confirm MVP does not expose ingestion as an MCP tool.

## Update rules

Update this file when tool facade methods, StructuredTool wrappers, agent state/nodes, adapter locations, future MCP constraints, or framework integration boundaries change.
