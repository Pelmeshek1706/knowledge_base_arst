# personal_kb

## Overview

`personal_kb` is a local-first personal knowledge base and GraphRAG system for organizing, indexing, retrieving, and answering questions over project documents.

## What This Project Does

- Discovers local documents.
- Normalizes and stores processed JSON in `kb_storage`.
- Builds graph/vector search structures in Neo4j.
- Provides retrieval and Q&A services.
- Exposes agent-facing tools through `KnowledgeToolService`.
- Uses LangGraph for internal agent orchestration.

## MVP Scope

Implemented or planned for MVP:

- deterministic local ingestion;
- processed JSON storage;
- Neo4j graph/vector sync;
- retrieval core;
- QA service;
- LangChain StructuredTools;
- LangGraph agent;
- CLI integration;
- benchmark/evaluation flow.

## Non-Goals

- No production cloud deployment in MVP.
- No MCP as primary internal runtime path in MVP.
- No runtime agent control over ingestion/rebuild/sync/delete/write actions.
- No uncontrolled document mutation by agents.

## Architecture Summary

```text
User
→ LangGraph personal_kb agent
→ LangChain StructuredTools
→ KnowledgeToolService
→ RetrievalService / QAService / GraphService
→ Neo4j + kb_storage + local models
```

## Agentic Development Workflow

```text
User request
→ Tech Lead plan
→ User approval required
→ Python Engineer executes exactly one approved task
→ QA Engineer reviews exactly one completed task
→ Fix/verify loop if needed
→ Final report
→ Explicit approval required before next task
```

## Testing and Validation

```bash
uv run pytest -q
```

Optional:

```bash
uv run ruff check .
uv run mypy src
```
