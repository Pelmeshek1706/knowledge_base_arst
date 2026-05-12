# Phase 4: Chunking + Processed JSON

## Purpose

Create format-aware chunks and persist processed documents to
`kb_storage/documents/<document_id>.json`.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 3: Parsers + Normalization](phase-03-parsers-normalization.md)

## Outputs

```text
personal_kb/ingestion/
  chunking_service.py
  processed_document_builder.py
```

## In scope

- Format-aware chunking.
- Processed document building.
- Processed JSON persistence under `kb_storage/documents/`.
- Stable chunk IDs within one processed document.
- Source references sufficient for user-facing citations.
- Skip behavior for unchanged files.

## Out of scope

- LLM extraction.
- Embedding generation.
- Neo4j sync.
- Retrieval and Q&A.

## Related docs

- [Roadmap index](index.md)
- [Storage design](../architecture/storage-design.md)
- [Phase 6: Extraction + Embeddings](phase-06-extraction-embeddings.md)
- [Phase 7: Neo4j Setup + Graph Sync](phase-07-neo4j-setup-graph-sync.md)

## Source of truth

This file is authoritative for Phase 4 chunking and processed JSON roadmap
scope.

## Implementation checklist

Chunking strategy:

| File type | Strategy |
|---|---|
| PDF | page-aware chunks |
| DOCX | heading-aware chunks |
| Markdown | heading-aware chunks |
| TXT | fixed-size chunks |
| XLSX | sheet/table/range chunks |

Processed JSON must contain:

- document metadata
- raw text
- chunks with full text
- chunk source references
- empty or populated tags/entities
- embeddings when generated
- processing metadata
- relationships when known

## Exit criteria

- Documents can be parsed, chunked, and saved without Neo4j.
- Chunk IDs are stable within one processed document.
- Source references are enough for user-facing citations.
- Re-running on unchanged files skips work.

## Validation

- Parse, chunk, and save documents without Neo4j.
- Confirm chunk IDs remain stable within one processed document.
- Confirm source references are sufficient for citations.
- Re-run ingestion on unchanged files and confirm work is skipped.

## Failure modes / risks

- Weak chunk source references can break citations later.
- Chunk ID instability can make graph sync and benchmark comparisons noisy.
- Making Neo4j a dependency here would weaken the `kb_storage` source-of-truth
  boundary.

## Update rules

Update this file when chunking strategy, processed JSON content, source
reference requirements, or skip behavior changes.
