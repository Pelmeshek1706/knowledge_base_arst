# Q&A Design

## Purpose

This file defines the source-grounded Q&A architecture, supported query types, `answer_question` output contract, context return policy, answer validation, Q&A metrics, and Q&A risks.

## When to read this

Read this file when changing grounded answer generation, query-type handling, `answer_question`, citation/source-reference behavior, supporting chunk policy, missing-information behavior, warning behavior, FAQ memory plans, or Q&A validation.

## Related files

- [overview.md](overview.md)
- [retrieval-design.md](retrieval-design.md)
- [storage-design.md](storage-design.md)
- [graph-schema.md](graph-schema.md)
- [model-strategy.md](model-strategy.md)
- [agent-design.md](agent-design.md)

## Source of truth

This file is authoritative for Q&A query types, grounded answer generation, `answer_question` JSON output, context return policy, Q&A metrics, hallucination risk handling, and future FAQ/QA memory behavior.

## Content

### Responsibility

The Q&A layer answers questions using retrieved documents/chunks.

It must:

- use retrieval results as source context;
- answer from supporting chunks;
- return source documents and source references;
- expose missing information explicitly;
- include warnings for uncertainty, low confidence, or conflicts;
- limit top-k chunks to avoid context overload.

### Component boundaries

Q&A should not:

- ingest documents;
- parse files;
- mutate source files;
- expose setup, rebuild, or sync operations to the agent;
- answer without supporting chunks for document-text questions;
- silently omit source references.

Retrieval is defined in [retrieval-design.md](retrieval-design.md). Model calls for answer generation are defined in [model-strategy.md](model-strategy.md). Agent/tool exposure is defined in [agent-design.md](agent-design.md).

### Query types

| Query type | Example | Expected output |
|---|---|---|
| document lookup | "в каком документе есть X?" | list of documents + confidence |
| entity lookup | "кто такой У?" | synthesized answer + source documents |
| discussion lookup | "где обсуждали X?" | related documents/chunks/threads |
| document Q&A | "какие пункты WP2 в document_a.docx?" | answer grounded in chunks |
| relationship explanation | "как связаны A и B?" | graph-based explanation |
| financial lookup | "документы про счета и бюджеты" | ranked documents + tags/entities |

### `answer_question` output

```json
{
  "question": "What are the WP2 points in document_a.docx?",
  "answer": "...",
  "confidence": 0.84,
  "source_documents": [
    {
      "document_id": "doc_123",
      "title": "document_a.docx",
      "file_path": "data/document_a.docx",
      "source_refs": [
        {
          "file_path": "data/document_a.docx",
          "page": null,
          "section": "WP2",
          "sheet": null,
          "cell_range": null
        }
      ]
    }
  ],
  "supporting_chunks": [
    {
      "chunk_id": "chunk_7",
      "text": "...",
      "summary": "...",
      "score": 0.91,
      "source_ref": {
        "file_path": "data/document_a.docx",
        "section": "WP2"
      }
    }
  ],
  "missing_information": [],
  "warnings": []
}
```

### Context return policy

For Q&A about document text:

```text
return supporting_chunks.text
```

For document lookup:

```text
return chunk summary + source reference
```

Always limit top-k chunks to avoid context overload.

### Future FAQ/QA memory

Future behavior:

1. User asks question.
2. System searches FAQ memory first.
3. System verifies whether supporting documents changed.
4. If still valid, returns existing answer.
5. If stale, regenerates answer and updates FAQ entry.

Future graph structure:

```text
(:Question)-[:ANSWERED_BY]->(:Answer)
(:Answer)-[:SUPPORTED_BY]->(:Chunk)
(:Answer)-[:USES_DOCUMENT]->(:Document)
(:Question)-[:ABOUT]->(:Entity)
(:Question)-[:HAS_TAG]->(:Tag)
(:FAQEntry)-[:SIMILAR_TO]->(:FAQEntry)
```

FAQ/QA memory is not MVP scope, but graph/schema space should be preserved for it.

## Public API / Methods

This file defines the behavior of the `answer_question` capability exposed through:

- CLI `kb ask`
- LangChain `StructuredTool` wrappers
- future MCP server adapter

The implementation should live in core services such as `QAService`, called through `KnowledgeToolService` as described in [agent-design.md](agent-design.md).

## Inputs

- user question
- retrieval results from [retrieval-design.md](retrieval-design.md)
- supporting chunks with full text from [storage-design.md](storage-design.md)
- source references from chunks/documents
- local answer-generation model from [model-strategy.md](model-strategy.md)

## Outputs

- answer text
- confidence
- source documents
- source references
- supporting chunks
- missing information list
- warnings

## Side effects

MVP Q&A should not write FAQ entries, mutate documents, update external systems, or change graph structure. Future FAQ memory may save or update answer records after explicit architecture support exists.

## Testing requirements

Q&A metrics:

- answer relevance
- faithfulness
- citation/source correctness
- expected answer coverage
- hallucination rate

Q&A benchmark cases should check `expected_answer_contains`, `expected_entities`, and `expected_source_refs`.

## What this must not do

- Do not answer document-text questions without supporting chunks.
- Do not omit source documents and source references.
- Do not expose ingestion, setup, or graph rebuild functions as Q&A capabilities.
- Do not implement FAQ memory in MVP.
- Do not allow hallucinated answers to pass without warning.

## Extension points

- FAQ/QA memory search before retrieval.
- Staleness checks for previous answers.
- Regeneration of stale FAQ answers.
- Optional save/update FAQ entry after answer generation.
- Relationship explanation using graph paths.

## Dependencies

- retrieval outputs from [retrieval-design.md](retrieval-design.md)
- full chunk text and source references from [storage-design.md](storage-design.md)
- graph relationships from [graph-schema.md](graph-schema.md)
- local LLM answer generation from [model-strategy.md](model-strategy.md)
- `KnowledgeToolService` and LangGraph orchestration from [agent-design.md](agent-design.md)

## Failure modes / risks

| Failure or risk | Mitigation |
|---|---|
| no results | return empty result with explanation |
| low confidence | return warning |
| conflicting documents | return warnings and source list |
| hallucinated answers | answer only from supporting chunks |
| context overload | limit top-k chunks |
| stale FAQ answer in future memory | verify whether supporting documents changed before reuse |

## Validation

Validate Q&A by checking that:

- document-text questions include `supporting_chunks.text`;
- document lookup returns chunk summary and source reference rather than full text by default;
- source documents include `document_id`, `title`, `file_path`, and `source_refs`;
- missing information is explicit;
- warnings are returned for low confidence and conflicts;
- benchmark cases satisfy expected answer coverage and expected source references;
- hallucination rate is tracked;
- Q&A latency is tracked;
- FAQ memory is not implemented in MVP.

## Update rules

Update this file when query types, grounded answer behavior, `answer_question` schema, context return policy, source reference behavior, warnings, missing-information behavior, Q&A metrics, FAQ memory behavior, or Q&A failure modes change.
