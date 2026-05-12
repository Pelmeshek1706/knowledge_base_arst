# Tool Services

## Purpose

This file defines the tool-facing service layer for `personal_kb`: `KnowledgeToolService`, LangChain StructuredTool factory behavior, CLI read/query command integration, and future MCP adapter boundaries.

## When to read this

Read this when changing:

- `KnowledgeToolService` facade methods;
- LangChain StructuredTool wrappers;
- tool exposure rules;
- CLI search/ask/related/duplicates/status behavior;
- future MCP adapter behavior;
- adapter boundaries between tools and core services.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [retrieval-services.md](retrieval-services.md)
- [qa-services.md](qa-services.md)
- [graph-services.md](graph-services.md)
- [agent-services.md](agent-services.md)
- [../tool-contracts/index.md](../tool-contracts/index.md)

## Source of truth

This file is authoritative for the class-design view of `KnowledgeToolService`, LangChain StructuredTools, CLI tool-facing behavior, and future MCP adapter constraints.

## Content

### `KnowledgeToolService`

**File:** `tools/knowledge_tool_service.py`

This is the facade used by LangChain StructuredTools, CLI search commands, and future MCP adapter.

```python
class KnowledgeToolService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        qa_service: QAService,
        graph_service: GraphService,
        document_service: DocumentService,
        duplicate_service: DuplicateService,
        relationship_service: RelationshipService,
    ) -> None:
        ...

    def search_documents(self, request: SearchDocumentsRequest) -> SearchDocumentsResponse: ...
    def answer_question(self, request: AnswerQuestionRequest) -> AnswerQuestionResponse: ...
    def show_related_documents(self, request: RelatedDocumentsRequest) -> RelatedDocumentsResponse: ...
    def get_document_summary(self, request: DocumentSummaryRequest) -> DocumentSummaryResponse: ...
    def get_document_chunks(self, request: DocumentChunksRequest) -> DocumentChunksResponse: ...
    def find_duplicates(self, request: FindDuplicatesRequest) -> FindDuplicatesResponse: ...
    def explain_document_relationship(self, request: ExplainRelationshipRequest) -> ExplainRelationshipResponse: ...
```

Rules:

```text
KnowledgeToolService is allowed to coordinate services.
It should not implement Cypher, parsing, chunking, model inference, or scoring directly.
```

### LangChain StructuredTools

**File:** `tools/langchain_tools.py`

Responsibility:

- Expose Personal KB capabilities to LangGraph agent.
- Wrap `KnowledgeToolService` methods as LangChain `StructuredTool` objects.
- Use Pydantic args schemas.

```python
class LangChainToolFactory:
    def __init__(self, tool_service: KnowledgeToolService) -> None:
        self.tool_service = tool_service

    def create_tools(self) -> list[StructuredTool]:
        return [
            self.create_search_documents_tool(),
            self.create_answer_question_tool(),
            self.create_show_related_documents_tool(),
            self.create_get_document_summary_tool(),
            self.create_get_document_chunks_tool(),
            self.create_find_duplicates_tool(),
            self.create_explain_document_relationship_tool(),
        ]
```

Allowed MVP tools:

```text
search_documents
answer_question
show_related_documents
get_document_summary
get_document_chunks
find_duplicates
explain_document_relationship
```

Not exposed to LangGraph agent:

```text
ingest_documents
rebuild_graph_from_manifest
sync_neo4j_from_json
delete_document
move_file
rename_file
send_email
update_confluence_page
create_jira_task
```

### CLI layer

#### CLI commands

**File:** `cli/main.py`, `cli/commands.py`

```bash
kb setup-db
kb ingest data
kb ingest data --auto-setup-db
kb search "accounting budget"
kb ask "Where is information about WP2?"
kb related --doc-id <uuid>
kb duplicates
kb status
```

#### CLI classes/functions

```python
class CLIApp:
    def run(self, argv: list[str] | None = None) -> int: ...
```

Command handlers should be thin:

```python
def handle_search(args: argparse.Namespace, tool_service: KnowledgeToolService) -> int:
    request = SearchDocumentsRequest(query=args.query)
    response = tool_service.search_documents(request)
    print_response(response, json_output=args.json)
    return 0
```

CLI ingestion commands call `IngestionService` directly, not agent tools.

### Future MCP adapter

**File:** `adapters/mcp/server.py`

MCP is not the primary MVP internal execution path.

Future role:

```text
External MCP-compatible agent/client
-> personal_kb MCP server adapter
-> KnowledgeToolService
-> core services
```

Rules:

- MCP tools must reuse the same Pydantic schemas.
- MCP tools must call `KnowledgeToolService`.
- MCP must not duplicate business logic.
- MCP server should expose the same read-only capabilities as LangChain StructuredTools.

Future MCP tools:

```text
search_documents
answer_question
show_related_documents
get_document_summary
get_document_chunks
find_duplicates
explain_document_relationship
```

Future external source MCP clients:

```text
Confluence MCP client
Jira MCP client
Gmail MCP client
Google Drive MCP client
```

These are outside MVP.

## Public API / Methods

- `KnowledgeToolService.search_documents`
- `KnowledgeToolService.answer_question`
- `KnowledgeToolService.show_related_documents`
- `KnowledgeToolService.get_document_summary`
- `KnowledgeToolService.get_document_chunks`
- `KnowledgeToolService.find_duplicates`
- `KnowledgeToolService.explain_document_relationship`
- `LangChainToolFactory.create_tools`
- `CLIApp.run`
- Thin CLI command handlers such as `handle_search`

## Inputs

- Pydantic request schemas.
- CLI args from `argparse`.
- LangChain StructuredTool args.
- Future MCP tool requests.

## Outputs

- Pydantic response schemas.
- JSON-serializable tool outputs.
- CLI-rendered responses through a renderer, not through core service logic.

## Side effects

- Tool services delegate to retrieval, Q&A, graph, document, duplicate, and relationship services.
- CLI ingestion commands may call `IngestionService` directly.
- LangChain and future MCP wrappers should not perform business logic side effects directly.

## Dependencies

- Search and Q&A schemas from [schemas.md](schemas.md).
- `RetrievalService` from [retrieval-services.md](retrieval-services.md).
- `QAService` from [qa-services.md](qa-services.md).
- `GraphService` from [graph-services.md](graph-services.md).
- Agent workflow from [agent-services.md](agent-services.md).
- Tool contract details in [../tool-contracts/index.md](../tool-contracts/index.md).

## Failure modes / risks

- Tool wrappers may accidentally accumulate Cypher, scoring, parsing, or model logic.
- CLI handlers may become business logic containers instead of thin adapters.
- Future MCP may duplicate logic instead of reusing `KnowledgeToolService`.
- Exposing ingestion or mutation tools to LangGraph would violate MVP safety boundaries.
- Request/response schema drift can break CLI, LangChain, and future MCP callers.

## Validation

- Tool wrapper tests verify calls delegate to `KnowledgeToolService`.
- CLI search/ask handlers create request schemas and render responses only.
- Allowed StructuredTools list contains only read/query tools.
- Future MCP adapter tests should prove the same Pydantic schemas and facade methods are reused.

## Testing requirements

- Unit-test `KnowledgeToolService` delegation.
- Unit-test StructuredTool args schema wiring.
- Unit-test CLI command handlers with mocked services.
- Contract-test JSON serialization of tool responses.

## What this must not do

- `KnowledgeToolService` must not implement Cypher, parsing, chunking, model inference, or scoring directly.
- Tool wrappers must not contain business logic.
- LangGraph agent must not receive mutation tools in MVP.
- MCP must not be the primary MVP internal execution path.
- CLI handlers must not call LangGraph for ingestion.

## Extension points

- Add future read-only tool methods through `KnowledgeToolService` first.
- Add future MCP server adapter over the same facade and schemas.
- Add UI/API/Telegram adapters as thin callers of the same service facade.

## Update rules

Update this file whenever facade methods, allowed tool exposure, StructuredTool wrapper behavior, CLI tool-facing behavior, future MCP constraints, or adapter boundaries change.
