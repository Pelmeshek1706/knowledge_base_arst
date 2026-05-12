# Q&A Services

## Purpose

This file defines the source-grounded Q&A service classes for `personal_kb`: context building, answer generation, and orchestration through `QAService`.

## When to read this

Read this when changing:

- answer context construction;
- supporting chunk selection;
- answer generation prompts or behavior;
- missing-information and warning behavior;
- source citation requirements;
- Q&A service orchestration.

## Related files

- [index.md](index.md)
- [overview.md](overview.md)
- [schemas.md](schemas.md)
- [retrieval-services.md](retrieval-services.md)
- [model-extraction-services.md](model-extraction-services.md)
- [tool-services.md](tool-services.md)
- [../../architecture/qa-design.md](../../architecture/qa-design.md)

## Source of truth

This file is authoritative for context building, grounded answer generation, and `QAService` class design.

## Content

### `ContextBuilder`

**File:** `qa/context_builder.py`

Responsibility:

- Convert search results into answer context.
- Control whether chunk text is included.
- Limit top-k chunks.

```python
class ContextBuilder:
    def build_context(self, search_response: SearchDocumentsResponse, include_text: bool, top_k_chunks: int) -> QAContext:
        ...
```

### `AnswerGenerator`

**File:** `qa/answer_generator.py`

Responsibility:

- Generate grounded answer using LM Studio LLM.
- Must use supporting chunks only.
- Must return warnings for missing/low-confidence information.

```python
class AnswerGenerator:
    def generate(self, question: str, context: QAContext) -> AnswerQuestionResponse:
        ...
```

### `QAService`

**File:** `qa/qa_service.py`

Responsibility:

- Orchestrate retrieval + answer generation.

```python
class QAService:
    def answer_question(self, request: AnswerQuestionRequest) -> AnswerQuestionResponse:
        ...
```

Dependencies:

```text
RetrievalService
ContextBuilder
AnswerGenerator
```

## Public API / Methods

- `ContextBuilder.build_context`
- `AnswerGenerator.generate`
- `QAService.answer_question`

## Inputs

- `AnswerQuestionRequest`.
- `SearchDocumentsResponse`.
- `include_text` / `include_supporting_chunk_text`.
- `top_k_chunks`.
- `QAContext`.
- Question text.

## Outputs

- `QAContext`.
- `AnswerQuestionResponse` with:
  - `question`;
  - `answer`;
  - `confidence`;
  - `source_documents`;
  - `supporting_chunks`;
  - `missing_information`;
  - `warnings`.

## Side effects

- Calls `RetrievalService`.
- Calls local LLM through `AnswerGenerator`.
- Does not ingest files, sync graph data, mutate source files, or expose write tools.

## Dependencies

- `AnswerQuestionRequest`, `AnswerQuestionResponse`, `SourceDocumentRef`, `MatchedChunk`, and `SearchDocumentsResponse` from [schemas.md](schemas.md).
- `RetrievalService` from [retrieval-services.md](retrieval-services.md).
- `LLMClient` from [model-extraction-services.md](model-extraction-services.md).
- `KnowledgeToolService.answer_question` delegates to Q&A in [tool-services.md](tool-services.md).

## Failure modes / risks

- Retrieval may return insufficient context.
- Supporting chunks may lack text when `include_supporting_chunk_text` is false.
- LLM output may be low-confidence or unsupported.
- Q&A must return `missing_information` and `warnings` instead of hallucinating.
- Answer generation must use supporting chunks only.

## Validation

- Verify context contains only selected top-k chunks.
- Verify answer source documents and source refs match supporting chunks.
- Verify missing or low-confidence information appears in `missing_information` / `warnings`.
- Verify answer generation does not cite unsupported sources.

## Testing requirements

- Unit-test `ContextBuilder` chunk selection and `include_text` behavior.
- Unit-test `AnswerGenerator` with mocked grounded and insufficient contexts.
- Integration-test `answer_question` returns grounded answer + source refs.
- Benchmark answer quality with:
  - answer faithfulness;
  - citation correctness;
  - latency.

## What this must not do

- `QAService` must not ingest files.
- `QAService` must not mutate Neo4j or processed JSON.
- `AnswerGenerator` must not use evidence outside supporting chunks.
- Q&A classes must not depend on LangChain StructuredTool, LangGraph, CLI, or future MCP.

## Extension points

- Add richer `QAContext` fields while preserving source references.
- Add answer formatting adapters outside core Q&A services.
- Add constrained document-ID Q&A only through validated request schemas and retrieval filters.

## Update rules

Update this file whenever Q&A request/response behavior, context-building rules, answer grounding, source citation, missing-information handling, or Q&A validation changes.
