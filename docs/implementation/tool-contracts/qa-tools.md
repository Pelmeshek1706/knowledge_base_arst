# Q&A Tools

## Purpose

This file defines the source-grounded Q&A tool contract and the `QAService` methods used to retrieve context, build prompts, validate grounding, and return cited answers.

## When to read this

Read this when changing:

- `answer_question`;
- grounded answer generation;
- supporting chunk retrieval for Q&A;
- answer prompt construction;
- citation behavior;
- Q&A confidence or warnings;
- `QAService` dependencies or methods.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [search-plan.md](search-plan.md)
- [knowledge-tool-service.md](knowledge-tool-service.md)
- [retrieval-tools.md](retrieval-tools.md)
- [langchain-structured-tools.md](langchain-structured-tools.md)
- [future-mcp-adapter.md](future-mcp-adapter.md)

## Source of truth

This file is authoritative for `answer_question` behavior and `QAService` methods. Shared `AnswerQuestionRequest` and `AnswerQuestionResponse` fields are defined in [knowledge-tool-service.md](knowledge-tool-service.md).

## Content

## Public API / Methods

### `answer_question`

#### Purpose

Answer a question using retrieved documents and chunks.

This is the main tool for questions like:

```text
What are the WP2 points in document_a.docx?
Who is Penelope according to our documents?
What does this document say about budget constraints?
Summarize what we know about accounting documents.
```

#### Layer ownership

| Layer | Responsibility |
|---|---|
| LangChain StructuredTool | validates input and calls `KnowledgeToolService` |
| KnowledgeToolService | delegates to `QAService` |
| QAService | retrieves context, builds prompt, calls local LLM, builds citations |
| RetrievalService | finds relevant documents/chunks |
| GraphService | retrieves chunks/source refs/related graph evidence |
| LLMClient | generates answer from context |
| CitationBuilder | attaches source references |

#### Function signature

```python
def answer_question(request: AnswerQuestionRequest) -> AnswerQuestionResponse:
    ...
```

StructuredTool wrapper signature:

```python
def answer_question(
    question: str,
    search_plan: dict | None = None,
    document_ids: list[str] | None = None,
    include_supporting_text: bool = True,
    top_k_chunks: int = 8,
) -> dict:
    ...
```

#### Dependencies

```text
QAService
RetrievalService
GraphService
LLMClient
CitationBuilder
PromptBuilder
```

#### Side effects

None in MVP.

Future QA/FAQ memory may add optional side effects such as storing a reusable answer, but this is not MVP scope.

#### Output

Returns answer, confidence, source documents, supporting chunks, missing information, and warnings.

#### Errors

| Error | Meaning | Recommended handling |
|---|---|---|
| `NoContextFoundError` | no supporting documents/chunks found | return empty answer with missing information |
| `LLMUnavailableError` | local LM Studio endpoint unavailable | return tool error |
| `LowConfidenceAnswerWarning` | context exists but answer confidence is low | return answer with warning |
| `CitationBuildError` | citation mapping failed | return answer with warning and raw source refs if possible |

#### Used by

```text
LangGraph AnswerNode
CLI: kb ask
Future MCP: answer_question
Future API: /ask or /chat
Q&A benchmark evaluation
```

### `QAService`

`QAService` owns source-grounded answer generation.

#### Dependencies

```text
RetrievalService
DocumentService
LLMClient
PromptBuilder
CitationBuilder
```

#### Methods

##### `answer_question(request)`

Purpose: generate an answer from retrieved context.

Steps:

```text
1. Determine whether question is constrained to specific documents.
2. Retrieve supporting chunks.
3. Build answer prompt from question and context.
4. Call local LLM.
5. Validate that the answer is grounded in context.
6. Build source document list and citations.
7. Return AnswerQuestionResponse.
```

Used by:

```text
KnowledgeToolService.answer_question
LangGraph AnswerNode
CLI kb ask
Future MCP answer_question
```

##### `retrieve_context(question, search_plan, document_ids)`

Purpose: get the chunks used for Q&A.

Calls:

```text
RetrievalService.search_documents
DocumentService.get_document_chunks
```

Used by:

```text
answer_question
```

##### `build_answer_prompt(question, supporting_chunks)`

Purpose: create the LLM prompt for grounded answer generation.

Calls:

```text
AnswerPromptBuilder.build
```

Used by:

```text
answer_question
```

##### `validate_answer(answer, supporting_chunks)`

Purpose: basic answer safety/grounding validation.

MVP behavior:

```text
- ensure answer is not empty
- ensure at least one source exists
- attach low-confidence warning if evidence is weak
```

Future behavior:

```text
- citation-level faithfulness scoring
- LLM judge or entailment check
```

## Dependencies

- `KnowledgeToolService`
- `QAService`
- `RetrievalService`
- `GraphService`
- `DocumentService`
- `LLMClient`
- `PromptBuilder`
- `AnswerPromptBuilder`
- `CitationBuilder`
- `SearchPlan`

## Failure modes / risks

- `NoContextFoundError`: no supporting documents/chunks found.
- `LLMUnavailableError`: local LM Studio endpoint unavailable.
- `LowConfidenceAnswerWarning`: context exists but answer confidence is low.
- `CitationBuildError`: citation mapping failed.
- Answer generation invents unsupported facts instead of answering from retrieved context.
- `supporting_chunks.text` is omitted for document-text Q&A.
- Future QA/FAQ memory side effects are added before MVP scope allows them.

## Validation

Verify:

- `answer_question` returns answer, confidence, source documents, supporting chunks, missing information, and warnings.
- document-text Q&A returns `supporting_chunks.text`.
- no-context questions return an empty answer with missing information.
- low-confidence answers include warnings.
- citation mapping failures return warnings and raw source refs if possible.
- answers are grounded in retrieved context.

## Update rules

Update this file when Q&A request handling, answer output, grounding validation, prompt building, citation behavior, confidence/warning behavior, LLM dependencies, or future Q&A side effects change.

## Inputs

- `AnswerQuestionRequest`
- `question`
- `search_plan`
- `document_ids`
- `include_supporting_text`
- `top_k_chunks`
- supporting chunks retrieved from `RetrievalService` and `DocumentService`

## Outputs

- `AnswerQuestionResponse`
- answer text
- confidence
- source documents
- supporting chunks
- missing information
- warnings

## Side effects

None in MVP.

## Testing requirements

Integration tests must cover:

```text
answer_question returns answer with supporting chunks
```

Q&A tests must also cover no-context behavior, low-confidence warnings, citation errors, constrained document Q&A, and response serialization.

## What this must not do

- Invent unsupported facts.
- Generate answers without sources.
- Modify documents.
- Trigger ingestion.
- Store QA/FAQ memory in MVP.
- Put prompt construction, LLM calls, or citation building inside tool wrappers.

## Extension points

- Future QA/FAQ memory with explicit side-effect design.
- Citation-level faithfulness scoring.
- LLM judge or entailment check.
- Future MCP, API, and chat adapters over the same `KnowledgeToolService.answer_question` contract.
