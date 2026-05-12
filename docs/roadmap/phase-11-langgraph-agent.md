# Phase 11: LangGraph Agent

## Purpose

Implement the MVP internal agent orchestration layer.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 10: KnowledgeToolService + StructuredTools](phase-10-knowledge-tool-service-structured-tools.md)

## Outputs

```text
personal_kb/agent/
  state.py
  query_router.py
  search_plan_builder.py
  graph.py
  nodes.py
```

## In scope

- Agent state.
- Query router.
- Search plan builder.
- LangGraph graph.
- Agent nodes.
- StructuredTool-based tool execution.
- Structured responses suitable for CLI or future API.

## Out of scope

- Direct repository or service access from the agent.
- Ingestion commands.
- Rebuild commands.
- Sync commands.
- Destructive file operations.

## Related docs

- [Roadmap index](index.md)
- [Agent design](../architecture/agent-design.md)
- [Class design agent services](../implementation/class-design/agent-services.md)
- [Phase 12: CLI Integration](phase-12-cli-integration.md)

## Source of truth

This file is authoritative for Phase 11 agent flow, routing examples, and
agent boundary roadmap scope.

## Implementation checklist

MVP agent flow:

```text
User question
-> QueryRouterNode
-> SearchPlanBuilderNode
-> ToolExecutionNode
-> OptionalAnswerNode
-> ResponseFormatterNode
```

Routing examples:

| Query type | Tool path |
|---|---|
| document lookup | `search_documents` |
| document Q&A | `search_documents` -> `answer_question` |
| related documents | `show_related_documents` |
| relationship explanation | `explain_document_relationship` |
| duplicate inspection | `find_duplicates` |

## Exit criteria

- Agent uses LangChain `StructuredTool` objects.
- Agent does not access repositories or services directly.
- Agent does not call ingestion/rebuild/sync commands.
- Agent returns structured responses suitable for CLI or future API.

## Validation

- Test routing examples and confirm expected tool paths.
- Confirm the agent uses LangChain `StructuredTool` objects.
- Inspect agent nodes for direct repository or service access.
- Confirm ingestion, rebuild, sync, and destructive file operations are not
  reachable from the agent.
- Confirm responses are structured for CLI or future API consumption.

## Failure modes / risks

- Tool business logic leakage can reappear if the agent bypasses
  `StructuredTool` wrappers.
- Giving the agent ingestion, rebuild, sync, or destructive file operations
  violates the MVP boundary.

## Update rules

Update this file when agent modules, node flow, routing examples, or agent
boundary rules change.
