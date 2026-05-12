# Phase 9: QA Service

## Purpose

Answer questions using retrieved chunks and graph context.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 8: Retrieval Core](phase-08-retrieval-core.md)

## Outputs

```text
personal_kb/qa/
  qa_service.py
  context_builder.py
  answer_generator.py
  citation_builder.py
```

## In scope

- Retrieved chunks as grounding context.
- Graph context where available from retrieval.
- Source-only answer generation.
- Supporting chunks and source references.
- Missing information and low-confidence warnings.
- Citation building.

## Out of scope

- Answering from model prior knowledge when sources are missing.
- FAQ/QA memory.
- Tool wrapper implementation.
- Agent orchestration.

## Related docs

- [Roadmap index](index.md)
- [QA design](../architecture/qa-design.md)
- [Tool contracts QA tools](../implementation/tool-contracts/qa-tools.md)
- [Phase 10: KnowledgeToolService + StructuredTools](phase-10-knowledge-tool-service-structured-tools.md)

## Source of truth

This file is authoritative for Phase 9 Q&A service behavior and source
grounding roadmap scope.

## Implementation checklist

Required behavior:

- Use retrieved chunks as grounding context.
- Return `supporting_chunks.text` for document-text Q&A.
- Return chunk summary + source reference for document lookup.
- Return warnings for low confidence or missing information.
- Do not answer from model prior knowledge when sources are missing.

## Exit criteria

- `answer_question` returns answer, confidence, source documents, supporting
  chunks, missing information, and warnings.
- Source references point to file path + page/section/sheet/cell range.
- Low-confidence answers include warning.
- Hallucination risk is reduced by source-only prompting.

## Validation

- Ask questions with known supporting chunks and confirm answer, confidence,
  source documents, supporting chunks, missing information, and warnings are
  returned.
- Confirm source references include file path plus page, section, sheet, or
  cell range as applicable.
- Test low-confidence cases and confirm warnings are present.
- Test missing-source cases and confirm the model does not answer from prior
  knowledge.

## Failure modes / risks

- Slow local models can affect Q&A latency.
- Hallucination risk must be mitigated by source-only prompting.
- Missing source references make answers difficult to verify.

## Update rules

Update this file when Q&A grounding, citation, confidence, warning, or
missing-information behavior changes.
