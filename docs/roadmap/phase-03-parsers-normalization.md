# Phase 3: Parsers + Normalization

## Purpose

Convert files into normalized `RawDocument` records with source references.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 2: Local Discovery + Hashing](phase-02-local-discovery-hashing.md)

## Outputs

```text
personal_kb/parsers/
  base.py
  txt_parser.py
  markdown_parser.py
  pdf_parser.py
  docx_parser.py
  xlsx_parser.py
  parser_registry.py
```

## In scope

- TXT parsing.
- Markdown parsing.
- PDF parsing with fallback.
- DOCX parsing with fallback.
- XLSX parsing.
- Parser registry.
- Source references for pages, sections, sheets, and cell ranges where
  applicable.

## Out of scope

- OCR for scanned PDFs.
- Chunking.
- LLM extraction.
- Embeddings.
- Neo4j sync.

## Related docs

- [Roadmap index](index.md)
- [Storage design](../architecture/storage-design.md)
- [Phase 4: Chunking + Processed JSON](phase-04-chunking-processed-json.md)

## Source of truth

This file is authoritative for Phase 3 parser deliverables, parser fallback
strategy, and parser acceptance criteria.

## Implementation checklist

Parser strategy:

| File type | Primary parser | Fallback | OCR |
|---|---|---|---|
| TXT | built-in | none | no |
| Markdown | built-in | none | no |
| PDF | `pdfplumber` | `PyMuPDF` | no |
| DOCX | `mammoth` | `python-docx` | no |
| XLSX | `openpyxl` | none | no |

## Exit criteria

- TXT and Markdown parsing works first.
- PDF page references are preserved.
- DOCX section/headings are preserved where possible.
- XLSX sheet and cell range references are preserved.
- Parser failures are saved to manifest with error details.

## Validation

- Parse representative TXT and Markdown files first.
- Parse PDF files and confirm page references are preserved.
- Parse DOCX files and confirm section/headings are preserved where possible.
- Parse XLSX files and confirm sheet and cell range references are preserved.
- Trigger parser failures and confirm manifest entries include error details.

## Failure modes / risks

- Lost source references weaken citations in retrieval and Q&A.
- Parser failures must not disappear; they must be visible in the manifest.
- OCR is explicitly out of scope for the MVP.

## Update rules

Update this file when supported formats, parser choices, fallback behavior,
source-reference requirements, or parser validation rules change.
