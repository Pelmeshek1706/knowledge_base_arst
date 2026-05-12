# LangChain Structured Tools

## Purpose

This file defines the MVP LangGraph agent contract and the LangChain StructuredTool wrapper rules used to expose `personal_kb` tools.

## When to read this

Read this when changing:

- LangGraph agent state;
- agent routing;
- agent nodes;
- tool registry behavior;
- LangChain StructuredTool wrappers;
- wrapper input schemas;
- wrapper serialization behavior.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [search-plan.md](search-plan.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [retrieval-tools.md](retrieval-tools.md)
- [qa-tools.md](qa-tools.md)
- [future-mcp-adapter.md](future-mcp-adapter.md)

## Source of truth

This file is authoritative for LangGraph orchestration responsibilities and LangChain StructuredTool wrapper constraints. Tool business behavior is owned by the focused retrieval and Q&A files.

## Content

### LangGraph agent contract

The MVP agent is responsible for orchestration, not business logic.

#### Agent state

Recommended state:

```python
class PersonalKBAgentState(TypedDict):
    user_query: str
    query_type: str | None
    search_plan: dict | None
    tool_calls: list[dict]
    tool_results: list[dict]
    final_response: dict | None
    warnings: list[str]
```

#### Nodes

##### `InputNode`

Purpose: receive user query and initialize state.

Dependencies:

```text
none
```

Used by:

```text
LangGraph entrypoint
```

##### `QueryRouterNode`

Purpose: classify the query into a tool route.

Possible routes:

```text
document_lookup
question_answering
related_documents
summary_lookup
chunk_lookup
duplicate_lookup
relationship_explanation
```

Dependencies:

```text
Rule-based classifier initially
Optional LLM classifier later
```

Used by:

```text
LangGraph agent before tool selection
```

##### `SearchPlanNode`

Purpose: build a `SearchPlan` suitable for the query type.

Dependencies:

```text
SearchPlanBuilder
Config
```

Used by:

```text
LangGraph agent before search/answer tool calls
```

##### `ToolExecutionNode`

Purpose: execute one or more LangChain StructuredTools.

Dependencies:

```text
LangChain StructuredTools
ToolRegistry
```

Used by:

```text
LangGraph agent after routing
```

##### `ResponseAssemblyNode`

Purpose: convert tool output into the final agent response.

Dependencies:

```text
none or response formatter
```

Used by:

```text
LangGraph final node
```

### LangChain StructuredTool contract

Each StructuredTool must be created from a small wrapper around `KnowledgeToolService`.

#### Example pattern

```python
search_documents_tool = StructuredTool.from_function(
    name="search_documents",
    description="Search personal_kb documents by keyword, entity, tag, vector similarity, and graph relationships.",
    func=search_documents_wrapper,
    args_schema=SearchDocumentsToolArgs,
)
```

#### Wrapper responsibilities

A wrapper may:

```text
validate input
construct request model
call KnowledgeToolService
serialize response
```

A wrapper must not:

```text
query Neo4j directly
read JSON files directly
call LLM directly
compute embeddings directly
compute scores directly
rerank candidates directly
```

## Dependencies

- LangGraph
- LangChain StructuredTool
- `KnowledgeToolService`
- `SearchPlanBuilder`
- `Config`
- `ToolRegistry`
- Pydantic wrapper argument schemas
- response formatter, if used

## Failure modes / risks

- Agent nodes accumulate business logic instead of orchestration.
- StructuredTool wrappers query Neo4j, read JSON, call LLMs, compute embeddings, compute scores, or rerank candidates directly.
- LangGraph route names drift from `SearchPlanBuilder.build_for_query_type(query_type)`.
- Tool output is not serialized consistently before returning to the agent.

## Validation

Verify:

- `InputNode` only receives and initializes state.
- `QueryRouterNode` only classifies route.
- `SearchPlanNode` delegates plan creation to `SearchPlanBuilder`.
- `ToolExecutionNode` executes registered StructuredTools.
- `ResponseAssemblyNode` converts tool output into the final agent response.
- each wrapper constructs request models, calls `KnowledgeToolService`, and serializes Pydantic responses.

## Update rules

Update this file when agent state fields, route names, node responsibilities, wrapper input schemas, wrapper serialization, tool registry behavior, or StructuredTool creation patterns change.

## Public API / Methods

- `PersonalKBAgentState`
- `InputNode`
- `QueryRouterNode`
- `SearchPlanNode`
- `ToolExecutionNode`
- `ResponseAssemblyNode`
- LangChain `StructuredTool.from_function(...)` wrappers

## Inputs

- user query;
- query type;
- optional `SearchPlan`;
- StructuredTool argument schemas;
- Pydantic request models.

## Outputs

- tool calls;
- tool results;
- final structured agent response;
- warnings;
- serialized Pydantic tool responses.

## Side effects

None beyond executing read-only MVP tools. The agent must not trigger ingestion or destructive actions in MVP.

## Testing requirements

Unit tests must cover StructuredTool wrapper calls.

Contract tests must cover:

```text
StructuredTool input schema matches Pydantic request schema
StructuredTool output can serialize to JSON
```

Agent tests should verify route selection, search-plan construction, tool execution, and response assembly without moving business logic into nodes.

## What this must not do

- Implement retrieval logic.
- Implement Q&A logic.
- Query Neo4j directly.
- Read processed JSON directly.
- Call local model clients directly.
- Compute embeddings, scores, or reranking.
- Trigger ingestion or destructive operations in MVP.

## Extension points

- Optional LLM classifier in `QueryRouterNode`.
- Additional route names when corresponding tools and `SearchPlanBuilder` behavior exist.
- Future adapters can reuse `KnowledgeToolService` without using LangGraph.
