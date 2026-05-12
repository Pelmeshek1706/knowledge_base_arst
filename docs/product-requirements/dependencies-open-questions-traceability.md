# Dependencies, Open Questions, and Traceability

## Purpose

This file lists Product Requirements dependencies, open product questions, and PRD-to-architecture traceability.

## When to read this

Read this when setting up the environment, resolving product ambiguities, or tracing PRD areas to architecture documentation.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Goals and scope](goals-and-scope.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Technical architecture](../../Technical_Architecture_Personal_KB_v0.3.md)

## Source of truth

This file is authoritative for Product Requirements dependencies, open product questions, and PRD-to-architecture traceability.

## Content

## Dependencies

### Runtime Dependencies

Expected implementation dependencies:

- Python 3.11
- uv
- argparse
- pydantic
- neo4j Python driver
- pdfplumber
- PyMuPDF fallback
- mammoth
- python-docx
- openpyxl
- transformers
- sentence-transformers
- local LM Studio OpenAI-compatible endpoint

### Infrastructure Dependencies

- Local Neo4j Docker Compose or existing local Neo4j.
- Target database: `knowledge_base3`, fallback `neo4j`.
- No APOC requirement.

## Open Product Questions

These are not blocking MVP start, but should be answered before later milestones:

1. What exact prompt format should be used for chunk summary/tag/entity extraction?
2. What confidence threshold should be used for low-confidence answers?
3. Should search results expose full chunk text only behind a flag?
4. What is the maximum document size allowed for MVP?
5. Should `kb status` include model availability checks?
6. Should benchmark evaluation be a CLI command: `kb eval benchmark/`?
7. Should document title be inferred from filename only, or from document content when available?
8. How should Excel merged cells and formulas be represented in chunk text?
9. Should embeddings be compressed or stored as float arrays in JSON v0.1?
10. Should failed Neo4j sync block ingestion or only mark `neo4j_synced=false`?

## PRD-to-Architecture Traceability

| PRD Area | Architecture Area |
|---|---|
| MVP scope | Technical Architecture Sections 1–4 |
| Local-first ingestion | Sections 5–12 |
| JSON processed storage | Section 6.5 |
| Neo4j graph/vector layer | Section 7 |
| Versioning/duplicates | Section 8 |
| Ingestion flow | Section 9 |
| File processing | Section 10 |
| Extraction | Section 11 |
| Graph sync | Section 12 |
| Search/Q&A | Sections 13–14 |
| Agent tools | Section 15 |
| LangGraph/StructuredTools/MCP boundary | Sections 15 and 23.6 |
| CLI | Section 16 |
| Configuration | Section 17 |
| Validation | Section 20 |
| Future extensions | Section 23 |

## Dependencies

- Root architecture document: `Technical_Architecture_Personal_KB_v0.3.md`.
- Runtime and infrastructure dependencies listed in this file.
- Focused PRD files linked from [index.md](index.md).

## Failure modes / risks

- Missing runtime dependencies can block implementation.
- Missing local Neo4j or LM Studio availability can block local validation.
- Unresolved open questions can affect later milestone behavior.
- Architecture sections can drift from PRD areas if traceability is not maintained.

## Validation

- Verify runtime dependencies are represented in project dependency files when implemented.
- Verify infrastructure assumptions match local setup documentation.
- Review open product questions before later milestones.
- Update traceability when architecture documents move or section numbering changes.

## Update rules

- Update this file when dependencies, infrastructure assumptions, open questions, or traceability mappings change.
- Update focused requirement files when an open question is resolved into behavior.
- Update links if architecture documentation is moved into `docs/architecture/`.
