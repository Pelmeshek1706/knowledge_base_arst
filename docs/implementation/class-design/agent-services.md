# Agent Services

## Purpose

This file defines the LangGraph agent class design for `personal_kb`: agent state, query routing, tool-call workflow, and orchestration boundaries.

## When to read this

Read this when changing:

- `PersonalKBAgentState`;
- query route types;
- deterministic or model-based routing;
- LangGraph workflow nodes;
- agent-to-tool boundaries;
- allowed agent capabilities.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [tool-services.md](tool-services.md)
- [retrieval-services.md](retrieval-services.md)
- [qa-services.md](qa-services.md)
- [../../architecture/agent-design.md](../../architecture/agent-design.md)

## Source of truth

This file is authoritative for LangGraph agent state, routing, and workflow class design.

## Content

### `agents/state.py`

```python
from typing import TypedDict, Any

class PersonalKBAgentState(TypedDict, total=False):
    user_query: str
    query_type: str
    search_plan: dict[str, Any]
    tool_results: list[dict[str, Any]]
    answer: str
    warnings: list[str]
```

### `QueryRouter`

**File:** `agents/router.py`

Responsibility:

- Classify user query type.
- Select search plan.
- Decide which tool should be called.

MVP can use deterministic routing first.

```python
class QueryRouter:
    def route(self, query: str) -> AgentRoute:
        ...
```

Example route types:

```text
document_lookup
question_answering
related_documents
summary_lookup
duplicate_lookup
relationship_explanation
```

### `PersonalKBLangGraphAgent`

**File:** `agents/langgraph_agent.py`

Responsibility:

- Build LangGraph workflow.
- Register LangChain StructuredTools.
- Execute query routing and tool calls.

MVP graph:

```text
InputNode
-> RouteQueryNode
-> ToolExecutionNode
-> ResponseFormattingNode
-> OutputNode
```

```python
class PersonalKBLangGraphAgent:
    def __init__(self, tools: list[StructuredTool], router: QueryRouter) -> None:
        ...

    def build_graph(self):
        ...

    def invoke(self, query: str) -> dict:
        ...
```

Important:

```text
LangGraph orchestrates.
LangChain StructuredTools expose schemas.
KnowledgeToolService executes capabilities.
Core services own business logic.
```

## Public API / Methods

- `QueryRouter.route`
- `PersonalKBLangGraphAgent.build_graph`
- `PersonalKBLangGraphAgent.invoke`

## Inputs

- User query string.
- `StructuredTool` list from `LangChainToolFactory`.
- `QueryRouter`.
- Agent state fields from `PersonalKBAgentState`.

## Outputs

- `AgentRoute`.
- Tool results in `PersonalKBAgentState`.
- Final agent response dictionary.
- Warnings collected from tool responses.

## Side effects

- Calls LangChain StructuredTools.
- Orchestrates tool execution through LangGraph.
- Does not parse files, sync graph data, delete files, move files, send email, or update external systems.

## Dependencies

- `LangChainToolFactory` and `KnowledgeToolService` from [tool-services.md](tool-services.md).
- Retrieval and Q&A capabilities exposed by [retrieval-services.md](retrieval-services.md) and [qa-services.md](qa-services.md).
- Agent architecture in [../../architecture/agent-design.md](../../architecture/agent-design.md).

## Failure modes / risks

- Agent route classification may choose the wrong tool.
- Agent state can lose warnings if response formatting is incomplete.
- Exposing mutation tools would make the agent control ingestion or external writes, which is outside MVP.
- Agent code must not become a business logic layer.

## Validation

- Verify each route type maps to an allowed tool.
- Verify agent workflow follows `InputNode -> RouteQueryNode -> ToolExecutionNode -> ResponseFormattingNode -> OutputNode`.
- Verify warnings from tool responses are preserved.
- Verify agent cannot call tools outside the allowed MVP list.

## Testing requirements

- Unit-test deterministic `QueryRouter` routes.
- Unit-test `PersonalKBLangGraphAgent.invoke` with mocked StructuredTools.
- Integration-test search and ask flows through the agent once tools are available.

## What this must not do

- `PersonalKBLangGraphAgent` must not parse or sync documents.
- `PersonalKBLangGraphAgent` must not delete, move, or rename source files.
- Agent services must not implement retrieval, scoring, graph traversal, or answer generation logic.
- Agent services must not depend directly on storage internals.

## Extension points

- Add route types only after corresponding read/query tool contracts exist.
- Replace deterministic routing with model-assisted routing after baseline route tests exist.
- Add future UI/API adapters outside the agent core.

## Update rules

Update this file whenever agent state, route types, workflow nodes, tool-call rules, or LangGraph orchestration behavior changes.
