# Phase 10: KnowledgeToolService + StructuredTools

## Purpose

Expose core functionality as stable tool contracts without putting business
logic inside tools.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 9: QA Service](phase-09-qa-service.md)

## Outputs

```text
personal_kb/tools/
  knowledge_tool_service.py
  structured_tools.py
  tool_registry.py
```

## In scope

- `KnowledgeToolService`.
- LangChain `StructuredTool` wrappers.
- Tool registry.
- MVP tool contracts.
- Pydantic input/output schemas for every tool.
- Adapter-only tool behavior.
- Unit tests with mocked services.

## Out of scope

- Business logic inside tools.
- Cypher in tools.
- Reranking in tools.
- Parsing in tools.
- LLM prompts in tools.
- Manifest business logic in tools.
- MCP server adapter implementation before core tools stabilize.

## Related docs

- [Roadmap index](index.md)
- [Tool contracts overview](../implementation/tool-contracts/overview.md)
- [KnowledgeToolService contract](../implementation/tool-contracts/knowledge-tool-service.md)
- [LangChain StructuredTool rules](../implementation/tool-contracts/langchain-structured-tools.md)
- [Future MCP adapter](../implementation/tool-contracts/future-mcp-adapter.md)
- [Phase 11: LangGraph Agent](phase-11-langgraph-agent.md)

## Source of truth

This file is authoritative for Phase 10 roadmap scope. The detailed tool
contracts are authoritative in [tool contracts](../implementation/tool-contracts/index.md).

## Implementation checklist

MVP tools:

```text
search_documents
answer_question
show_related_documents
get_document_summary
get_document_chunks
find_duplicates
explain_document_relationship
```

Tool rule:

Tools are adapters only.

```text
LangChain StructuredTool
-> validates request
-> calls KnowledgeToolService
-> returns Pydantic response as JSON-compatible dict
```

## Exit criteria

- Every tool has Pydantic input/output schema.
- Every tool delegates to `KnowledgeToolService`.
- Tools do not contain Cypher, reranking, parsing, LLM prompts, or manifest
  business logic.
- Tools are unit-tested with mocked services.

## Validation

- Confirm each MVP tool has Pydantic input/output schemas.
- Unit-test each tool with mocked `KnowledgeToolService`.
- Inspect tools for absence of Cypher, reranking, parsing, LLM prompts, and
  manifest business logic.
- Confirm responses are JSON-compatible dictionaries derived from Pydantic
  responses.

## Failure modes / risks

- Tool business logic leakage is a high-risk failure mode; tools must remain
  adapters only and `KnowledgeToolService` should be tested separately.
- Overbuilding MCP too early is explicitly post-MVP.

## Update rules

Update this file when MVP tool list, adapter rules, schema requirements, or
tool testing requirements change.
