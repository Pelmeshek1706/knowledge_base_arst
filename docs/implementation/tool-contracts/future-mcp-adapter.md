# Future MCP Adapter

## Purpose

This file defines the future MCP adapter boundary for `personal_kb`. MCP is post-MVP and must reuse the same core tool contracts and `KnowledgeToolService` facade used by LangChain StructuredTools.

## When to read this

Read this when planning or changing:

- MCP server exposure;
- MCP request conversion;
- MCP response serialization;
- post-MVP external tool access;
- future external source ingestion through MCP clients.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [retrieval-tools.md](retrieval-tools.md)
- [qa-tools.md](qa-tools.md)
- [langchain-structured-tools.md](langchain-structured-tools.md)

## Source of truth

This file is authoritative for future MCP adapter responsibilities and prohibitions. The underlying tool contracts remain authoritative in the focused retrieval, Q&A, search-plan, and facade files.

## Content

### MCP status

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

### Future MCP path

```text
External MCP client
-> personal_kb MCP server tool call
-> MCP adapter converter
-> KnowledgeToolService
-> same core services
-> structured response
```

### Future MCP tools

```text
search_documents
answer_question
show_related_documents
get_document_summary
get_document_chunks
find_duplicates
explain_document_relationship
```

### MCP adapter responsibilities

```text
1. Accept MCP tool input.
2. Convert input to Pydantic request model.
3. Call KnowledgeToolService.
4. Serialize Pydantic response to MCP-compatible output.
```

### MCP adapter must not

```text
implement a separate retrieval pipeline
implement a separate Q&A pipeline
bypass KnowledgeToolService
expose ingestion in MVP
expose destructive actions without confirmation in future
```

### MCP exposure summary

| Tool | Exposed to MCP in MVP | Side effects | Core service |
|---|---:|---:|---|
| `search_documents` | no | none | `RetrievalService` |
| `answer_question` | no | none | `QAService` |
| `show_related_documents` | no | none | `GraphService` + `DocumentService` |
| `get_document_summary` | no | none | `DocumentService` |
| `get_document_chunks` | no | none | `DocumentService` |
| `find_duplicates` | no | none | `DocumentService` + `GraphService` |
| `explain_document_relationship` | no | none | `GraphService` |

MCP exposure is post-MVP and should reuse the same core contracts.

## Dependencies

- MCP SDK, post-MVP only.
- `KnowledgeToolService`
- Pydantic request models
- Pydantic response models
- `RetrievalService`
- `QAService`
- `GraphService`
- `DocumentService`
- `kb_storage`
- Neo4j
- local model clients

## Failure modes / risks

- MCP becomes a second implementation of retrieval or Q&A.
- MCP bypasses `KnowledgeToolService`.
- MCP exposes ingestion during MVP.
- MCP exposes destructive actions later without confirmation.
- MCP response shape diverges from StructuredTool output.
- External source ingestion is treated as MVP scope.

## Validation

Future MCP contract tests must cover:

```text
Future MCP adapter returns same output shape as StructuredTool path
```

Also verify:

- MCP input converts to the same Pydantic request models;
- MCP output serializes the same Pydantic response models;
- MCP tools call `KnowledgeToolService`;
- no separate retrieval or Q&A pipeline exists in the MCP adapter;
- no ingestion or destructive actions are exposed in MVP.

## Update rules

Update this file when MCP exposure, MCP conversion rules, MCP response serialization, future external source ingestion assumptions, or post-MVP adapter constraints change.

## Public API / Methods

Future MCP tool names:

- `search_documents`
- `answer_question`
- `show_related_documents`
- `get_document_summary`
- `get_document_chunks`
- `find_duplicates`
- `explain_document_relationship`

## Inputs

- MCP tool input payloads.
- Converted Pydantic request models.

## Outputs

- MCP-compatible serialized Pydantic responses.

## Side effects

None for MVP-equivalent tools. Ingestion and destructive actions are not exposed in MVP.

## Testing requirements

Contract tests must compare future MCP output shape with the StructuredTool path and verify that all MCP tools route through `KnowledgeToolService`.

## What this must not do

- Replace LangGraph as the MVP internal execution path.
- Implement separate retrieval or Q&A logic.
- Bypass `KnowledgeToolService`.
- Expose ingestion in MVP.
- Expose destructive actions without confirmation in future.

## Extension points

- Post-MVP external MCP clients.
- Future external source ingestion through MCP clients into the `RawDocument` contract and deterministic ingestion pipeline.
