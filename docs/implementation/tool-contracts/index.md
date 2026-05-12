# Tool Contracts Index

## Purpose

This folder defines the tool contracts for `personal_kb`: the public tool surface, request/response schemas, service facade, retrieval and Q&A responsibilities, LangGraph/StructuredTool execution boundary, and future MCP adapter constraints.

## When to read this

Start here for:

- implementation planning for tool-facing behavior;
- tool contract changes;
- service facade changes;
- retrieval tool changes;
- grounded Q&A tool changes;
- LangGraph or LangChain StructuredTool integration changes;
- future MCP adapter planning;
- benchmark or contract-test updates involving tool outputs.

## Source of truth

| Topic | Authoritative file |
|---|---|
| Cross-cutting tool architecture, design rules, runtime flow, error model, testing requirements, and MVP exposure summary | [overview.md](overview.md) |
| `SearchPlan` and `SearchPlanBuilder` behavior | [search-plan.md](search-plan.md) |
| `KnowledgeToolService` facade and shared request/response contracts | [knowledge-tool-service.md](knowledge-tool-service.md) |
| Search, related-document, summary, chunk, duplicate, and relationship tool behavior | [retrieval-tools.md](retrieval-tools.md) |
| Grounded Q&A tool behavior and `QAService` methods | [qa-tools.md](qa-tools.md) |
| LangGraph agent orchestration and LangChain StructuredTool wrapper rules | [langchain-structured-tools.md](langchain-structured-tools.md) |
| Future MCP server adapter boundary | [future-mcp-adapter.md](future-mcp-adapter.md) |

## Reading order

1. Read [overview.md](overview.md) for the domain summary and global rules.
2. Read the focused file related to the current task.
3. Read related files listed in the focused document.
4. Do not scan the whole folder unless explicitly requested.

## Files

| Topic | File | Purpose |
|---|---|---|
| Overview | [overview.md](overview.md) | Explains the high-level tool architecture and cross-cutting rules. |
| Search planning | [search-plan.md](search-plan.md) | Defines `SearchPlan` and `SearchPlanBuilder`. |
| Tool facade | [knowledge-tool-service.md](knowledge-tool-service.md) | Defines the service facade and shared request/response contracts. |
| Retrieval tools | [retrieval-tools.md](retrieval-tools.md) | Defines search and document-inspection tool behavior. |
| Q&A tools | [qa-tools.md](qa-tools.md) | Defines source-grounded question answering behavior. |
| Structured tools | [langchain-structured-tools.md](langchain-structured-tools.md) | Defines LangGraph orchestration and LangChain wrapper constraints. |
| Future MCP adapter | [future-mcp-adapter.md](future-mcp-adapter.md) | Defines future MCP adapter responsibilities and prohibitions. |

## Update rules

- Update [search-plan.md](search-plan.md) when retrieval strategy fields, defaults, validation, or query-type plans change.
- Update [knowledge-tool-service.md](knowledge-tool-service.md) when request/response schemas or facade methods change.
- Update [retrieval-tools.md](retrieval-tools.md) when read-only search, relationship, summary, chunk, or duplicate behavior changes.
- Update [qa-tools.md](qa-tools.md) when answer generation, grounding, citation, or Q&A retrieval behavior changes.
- Update [langchain-structured-tools.md](langchain-structured-tools.md) when agent routes, state, nodes, tool registry, or wrapper rules change.
- Update [future-mcp-adapter.md](future-mcp-adapter.md) when MCP exposure or adapter conversion rules change.
- Update [overview.md](overview.md) when cross-cutting architecture, error, testing, or MVP exposure rules change.

## Do not read everything by default

Coding agents should open only the focused files needed for the current task. Use this index as the router.
