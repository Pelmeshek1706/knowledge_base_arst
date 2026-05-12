# Ingestion, Parsing, And Models

## Purpose

This file defines the repository areas for source-file parsing, chunking, local model clients, and deterministic ingestion orchestration.

## When to read this

Read this when implementing or changing `personal_kb/parsers/`, `personal_kb/chunking/`, `personal_kb/models/`, or `personal_kb/ingestion/`.

## Related files

- [core-schemas-storage.md](core-schemas-storage.md)
- [graph-retrieval-qa.md](graph-retrieval-qa.md)
- [project-root-and-runtime-data.md](project-root-and-runtime-data.md)
- [../class-design/core-storage-ingestion.md](../class-design/core-storage-ingestion.md)
- [../class-design/model-extraction-services.md](../class-design/model-extraction-services.md)

## Source of truth

This file is authoritative for repository structure and responsibilities of parsers, chunkers, model clients, and ingestion services.

## Content

## `personal_kb/parsers/`

Purpose:

- convert source files into `ParsedDocument`;
- preserve source references;
- avoid LLM logic.

### Parser registry

`registry.py` maps file extensions to parsers:

```text
.pdf  -> PdfParser
.docx -> DocxParser
.md   -> MarkdownParser
.txt  -> TextParser
.xlsx -> XlsxParser
```

### `pdf_parser.py`

Primary parser:

```text
pdfplumber
```

Fallback:

```text
PyMuPDF
```

OCR:

```text
not supported in MVP
```

Responsibilities:

- extract page-aware text;
- preserve page numbers;
- return empty/failed status for scanned PDFs.

### `docx_parser.py`

Primary parser:

```text
mammoth
```

Fallback:

```text
python-docx
```

Responsibilities:

- convert DOCX to clean text/HTML-derived structure;
- preserve headings where possible;
- extract raw paragraphs/tables with fallback.

### `xlsx_parser.py`

Primary parser:

```text
openpyxl
```

Responsibilities:

- treat workbook as `Document`;
- treat sheet as logical section/source ref;
- treat non-empty table/range as chunk candidate;
- preserve sheet name and cell range.

## `personal_kb/chunking/`

Purpose:

- create retrieval chunks from parsed documents;
- keep chunk source refs;
- avoid LLM/model calls.

### Chunking strategies

| File type | Strategy |
|---|---|
| PDF | page-aware chunks |
| DOCX | heading-aware chunks |
| Markdown | heading-aware chunks |
| TXT | fixed-size chunks |
| XLSX | sheet/table/range chunks |

### `base.py`

Defines interface:

```python
class BaseChunker(Protocol):
    def chunk(self, document: ParsedDocument) -> list[ChunkRecord]: ...
```

## `personal_kb/models/`

Purpose:

- isolate local model execution;
- prevent model-specific code from leaking into services.

### `llm_client.py`

Runtime:

```text
LM Studio OpenAI-compatible endpoint
```

Model:

```text
mlx-community/Qwen3.5-9B-OptiQ-4bit
```

Responsibilities:

- generate summaries;
- generate structured extraction outputs;
- generate Q&A answers;
- handle retry/JSON repair policy where appropriate.

### `embedding_client.py`

Model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Execution:

```text
transformers or sentence-transformers locally
```

Config:

```text
dimension: 1024
context_length: 32768
normalize_embeddings: true
instruction_aware: true
```

Responsibilities:

- embed chunks;
- embed queries;
- return normalized vectors;
- expose model metadata.

### `reranker_client.py`

Model:

```text
Qwen/Qwen3-Reranker-0.6B
```

Execution:

```text
transformers or sentence-transformers locally
```

Config:

```text
top_k_before_rerank: 50
top_k_after_rerank: 8
context_length: 32768
instruction_aware: true
```

Responsibilities:

- rerank document/chunk candidates;
- return reranker scores;
- allow fallback to hybrid formula if unavailable.

## `personal_kb/ingestion/`

Purpose:

- deterministic document processing pipeline;
- not controlled by the agent;
- called by `kb ingest`.

### `file_discovery.py`

Responsibilities:

- scan `data/`;
- filter supported extensions;
- return file candidates with relative paths.

### `ingestion_planner.py`

Responsibilities:

- compare discovered files with manifest;
- decide action:

```text
skip
process_new
create_newer_version
create_duplicate
mark_failed
```

Decision inputs:

- source path;
- raw bytes hash;
- extracted text hash when available;
- manifest entries.

### `ingestion_service.py`

Responsibilities:

- orchestrate full ingestion pipeline;
- call planner, parsers, chunkers, extraction, embeddings, storage, graph sync;
- update manifest.

Must not:

- be called by LangGraph agent in MVP;
- mutate source files.

### `document_processor.py`

Responsibilities:

- process one document candidate;
- parse;
- chunk;
- extract;
- embed;
- build `ProcessedDocument`.

### `duplicate_service.py`

Responsibilities:

- exact duplicate handling;
- create duplicate relationship records;
- keep duplicate as its own `Document` node.

### `versioning_service.py`

Responsibilities:

- handle changed file behavior;
- MVP default:

```text
auto NEWER_VERSION_OF
```

## Dependencies

- `data/`
- `kb_storage/`
- `configs/default.yaml`
- `personal_kb/core/hashing.py`
- `personal_kb/core/normalization.py`
- `personal_kb/schemas/processing.py`
- `personal_kb/schemas/chunk.py`
- `personal_kb/storage/manifest_store.py`
- `personal_kb/storage/processed_document_store.py`
- `personal_kb/graph/graph_sync_service.py`

## Failure modes / risks

- Scanned PDFs are not supported by OCR in the MVP and should return empty/failed status.
- Ingestion must not mutate source files under `data/`.
- Model-specific behavior can leak into services if clients are not isolated.
- Reranking must have a fallback to the hybrid formula if unavailable.
- Duplicate handling must keep duplicates as their own `Document` nodes.

## Validation

- Unit test parser registry mappings and chunking strategies.
- Integration test TXT/MD ingestion before expanding to PDF/DOCX/XLSX.
- Confirm `kb ingest data` creates per-document JSON for supported MVP files.
- Confirm processed JSON contains `summary`, `tags`, `entities`, `embeddings`, and processing metadata after model-client phases.
- Confirm source references preserve page, heading, sheet, and cell/range details where supported.

## Update rules

Update this file when supported file types, parser backends, chunking strategies, model choices/config, ingestion actions, duplicate/version behavior, or ingestion prohibitions change.
