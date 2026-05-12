# Python Class Design Index

## Purpose

This folder defines the Python class design for the `personal_kb` MVP: package boundaries, Pydantic contracts, service ownership, adapter boundaries, error behavior, testing expectations, and implementation order.

## When to read this

Start here for:

- architecture updates that affect Python package boundaries;
- implementation planning for schemas, storage, ingestion, graph, retrieval, Q&A, tools, agent, or CLI classes;
- class/service design changes;
- adapter boundary changes for LangChain, LangGraph, CLI, or future MCP;
- validation, testing, or benchmark changes that depend on service ownership.

## Source of truth

| Topic | Authoritative file |
|---|---|
| Cross-cutting class design, package structure, dependency direction, composition root, error model, testing strategy, implementation order, class matrix, and acceptance criteria | [overview.md](overview.md) |
| Pydantic schemas and configuration DTOs | [schemas.md](schemas.md) |
| Core utilities, storage stores, parsers, chunkers, and deterministic ingestion pipeline | [core-storage-ingestion.md](core-storage-ingestion.md) |
| Local model clients, structured extraction, and metadata aggregation | [model-extraction-services.md](model-extraction-services.md) |
| Neo4j driver, schema manager, graph sync, and graph query service | [graph-services.md](graph-services.md) |
| Retrieval orchestration, search subservices, and scoring | [retrieval-services.md](retrieval-services.md) |
| Q&A context building, answer generation, and source-grounded answer orchestration | [qa-services.md](qa-services.md) |
| `KnowledgeToolService`, LangChain StructuredTools, CLI search/ask behavior, and future MCP adapter | [tool-services.md](tool-services.md) |
| LangGraph state, routing, and agent workflow | [agent-services.md](agent-services.md) |

## Reading order

1. Read [overview.md](overview.md) for the domain summary and global class-design rules.
2. Read the focused file related to the current task.
3. Read related files listed in the focused document.
4. Do not scan the whole folder unless explicitly requested.

## Files

| Topic | File | Purpose |
|---|---|---|
| Overview | [overview.md](overview.md) | Explains the high-level class design, package layout, dependency direction, testing strategy, and implementation order. |
| Schemas | [schemas.md](schemas.md) | Defines shared Pydantic schemas and configuration classes. |
| Core, storage, ingestion | [core-storage-ingestion.md](core-storage-ingestion.md) | Defines deterministic local-file processing classes before graph/model retrieval. |
| Models and extraction | [model-extraction-services.md](model-extraction-services.md) | Defines local LLM, embedding, reranker, extraction, and aggregation classes. |
| Graph services | [graph-services.md](graph-services.md) | Defines Neo4j setup, sync, and query services. |
| Retrieval services | [retrieval-services.md](retrieval-services.md) | Defines document retrieval, search subservices, scoring, and reranking. |
| Q&A services | [qa-services.md](qa-services.md) | Defines source-grounded answer generation. |
| Tool services | [tool-services.md](tool-services.md) | Defines the tool facade, StructuredTool wrappers, CLI use, and future MCP adapter. |
| Agent services | [agent-services.md](agent-services.md) | Defines LangGraph agent state, query routing, and workflow orchestration. |

## Update rules

- Update [schemas.md](schemas.md) when any Pydantic model, config class, field, default, or schema module changes.
- Update [core-storage-ingestion.md](core-storage-ingestion.md) when local discovery, hashing, parsing, chunking, manifest, processed JSON, duplicate/version planning, or ingestion orchestration changes.
- Update [model-extraction-services.md](model-extraction-services.md) when local LLM, embedding, reranking, structured extraction, or metadata aggregation behavior changes.
- Update [graph-services.md](graph-services.md) when Neo4j setup, sync, graph query methods, graph prohibitions, or graph rebuild assumptions change.
- Update [retrieval-services.md](retrieval-services.md) when retrieval layers, scoring weights, reranking, or search result construction changes.
- Update [qa-services.md](qa-services.md) when answer grounding, context building, source citation, missing-information handling, or Q&A orchestration changes.
- Update [tool-services.md](tool-services.md) when tool facade methods, LangChain wrappers, CLI tool-facing behavior, or future MCP exposure changes.
- Update [agent-services.md](agent-services.md) when LangGraph state, route types, nodes, or agent orchestration changes.
- Update [overview.md](overview.md) when package boundaries, dependency direction, composition root, error policy, testing strategy, implementation order, or acceptance criteria change.

## Do not read everything by default

Coding agents should open only the focused files needed for the current task. Use this index as the router.
