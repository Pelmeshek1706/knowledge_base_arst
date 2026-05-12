# Product Requirements Overview

## Purpose

This file gives the high-level product context for Personal KB.

## When to read this

Read this before changing product direction, explaining the MVP, or orienting to the PRD.

## Related files

- [Product requirements index](index.md)
- [Goals and scope](goals-and-scope.md)
- [Validation and acceptance](validation-and-acceptance.md)
- [PRD-to-architecture traceability](dependencies-open-questions-traceability.md)
- [Technical architecture](../../Technical_Architecture_Personal_KB_v0.3.md)

## Source of truth

This file is authoritative for the Product Requirements executive summary, problem statement, and final MVP definition.

## Content

**Status:** Draft v0.2

**Product name:** Personal KB

**Package name:** `personal_kb`

**Related architecture:** `Technical_Architecture_Personal_KB_v0.3.md`

**Primary user:** Individual technical user who needs a local-first system for organizing, searching, and querying personal/work documents.

**MVP type:** Local-first CLI + agent-tool backend.

## Executive Summary

Personal KB is a local-first document organization and retrieval product for building a searchable knowledge base over personal and work documents.

The product ingests local files, extracts text and metadata, chunks content, generates summaries/tags/entities, stores processed state in JSON, syncs the resulting graph and vectors into Neo4j, and exposes search/Q&A through an internal LangGraph agent using LangChain StructuredTools over core Python services. MCP is planned as a later adapter, not as the primary internal MVP path.

The MVP focuses on reliable document processing and retrieval, not on UI polish or multi-source sync.

### Core MVP promise

Given a local folder with documents, the system should:

1. Process supported files into structured JSON.
2. Build a Neo4j graph linking documents, chunks, tags, entities, document types, versions, and duplicates.
3. Return relevant documents with confidence scores, summaries, tags, matched chunks, and source references.
4. Answer source-grounded questions using retrieved chunks.
5. Operate fully locally with local LLM, embedding, and reranker models.
6. Route MVP agent queries through LangGraph → LangChain StructuredTools → KnowledgeToolService → core services.

## Problem Statement

The user has documents spread across many sources and formats. Documents are not consistently organized, duplicates exist, and it is difficult to determine where a specific piece of information is stored.

Current pain points:

- Long time required to find the right document.
- Documents are not systematically organized.
- Duplicate documents are difficult to detect and manage.
- It is hard to answer questions like “where is X discussed?” or “which document contains information about Y?”.
- Documents are not linked to broader concepts, people, projects, tasks, or topics.
- Future sources such as Confluence, Jira, Gmail, and Google Drive need to be integrated into one unified memory layer.

## Final MVP Definition

The MVP is a local-first CLI/tool system that can process a folder of local documents, create a rebuildable JSON state, sync a deterministic Neo4j graph/vector index, and expose safe search/Q&A tools that return source-grounded structured JSON.

The first real milestone:

```text
Given 10–20 local documents and 15–20 benchmark questions,
personal_kb can ingest the documents, build JSON + Neo4j state,
and retrieve the expected documents in top-10 with source references.
```

## Dependencies

- Product goals and MVP scope are defined in [goals-and-scope.md](goals-and-scope.md).
- Acceptance criteria are defined in [validation-and-acceptance.md](validation-and-acceptance.md).
- Architecture mapping is defined in [dependencies-open-questions-traceability.md](dependencies-open-questions-traceability.md).

## Failure modes / risks

- Treating future connectors, MCP, or UI work as part of the MVP conflicts with the product definition.
- Implementing MCP as the primary internal MVP path conflicts with the stated MVP type.
- Returning ungrounded answers conflicts with the source-grounded Q&A promise.

## Validation

- Verify implementation plans still satisfy every item in the core MVP promise.
- Verify release plans align with the final MVP definition.
- Verify product changes do not expand MVP scope without updating [goals-and-scope.md](goals-and-scope.md).

## Update rules

- Update this file when the product summary, MVP type, problem statement, or final MVP definition changes.
- Update [goals-and-scope.md](goals-and-scope.md) when the change affects goals, non-goals, or scope.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when the MVP definition changes acceptance criteria.
