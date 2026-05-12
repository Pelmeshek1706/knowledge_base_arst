# Phase 2: Local Discovery + Hashing

## Purpose

Detect supported local files, identify new/changed/duplicate files, and decide
the ingestion action before expensive parsing or model calls.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 1: Schemas + Config + Manifest](phase-01-schemas-config-manifest.md)

## Outputs

```text
personal_kb/ingestion/
  file_discovery.py
  ingestion_decision.py

personal_kb/core/
  hashing.py
```

## In scope

- Supported-file scanning under `data/`.
- Raw bytes hashing with SHA256.
- Extracted text hashing with SHA256 after parsing.
- Pre-parse skip decisions for exact raw-byte duplicates.
- Post-parse decisions for changed text, duplicate text, or new processed
  documents.
- Retry behavior for previously failed documents.

## Out of scope

- Parser implementation.
- Chunking.
- Model calls.
- Neo4j graph relationships beyond the decisions recorded for later sync.

## Related docs

- [Roadmap index](index.md)
- [Storage design](../architecture/storage-design.md)
- [Phase 7: Neo4j Setup + Graph Sync](phase-07-neo4j-setup-graph-sync.md)

## Source of truth

This file is authoritative for Phase 2 discovery, hashing, duplicate/version,
and retry decision roadmap scope.

## Implementation checklist

Required functions/classes:

| Function/Class | Responsibility |
|---|---|
| `FileDiscoveryService.scan()` | List supported files under `data/`. |
| `HashingService.compute_raw_bytes_hash()` | SHA256 over file bytes. |
| `HashingService.compute_extracted_text_hash()` | SHA256 over normalized extracted text. Used after parsing. |
| `IngestionDecisionService.decide_pre_parse()` | Skip exact raw-byte duplicates before parsing. |
| `IngestionDecisionService.decide_post_parse()` | Decide changed text, duplicate text, or new processed document. |

Decision rules:

| Case | Detection | Behavior |
|---|---|---|
| Same path, same raw hash | Manifest match | Skip. |
| Same path, new raw hash | Same source path, different hash | Process as new document and create `NEWER_VERSION_OF`. |
| Different path, same raw hash | Same raw hash, different path | Create own `Document` node and `DUPLICATE_OF`. |
| Same extracted text hash | Same normalized text, different raw bytes | Treat as exact text duplicate. |
| Failed previous document | Existing failed manifest entry | Retry only if user passes retry flag or file changed. |

## Exit criteria

- Duplicate detection happens before LLM/embedding calls when possible.
- Changed files default to `NEWER_VERSION_OF`.
- Failed documents stay in manifest.
- No unsupported file types are processed.

## Validation

- Test same-path same-hash files are skipped.
- Test same-path changed files produce `NEWER_VERSION_OF` decisions.
- Test different-path same-hash files produce duplicate decisions.
- Test failed documents remain in the manifest and retry only with a retry flag
  or file change.
- Confirm unsupported file types are ignored.

## Failure modes / risks

- Duplicate/version confusion can propagate into graph relationships.
- Missing pre-parse skip logic can waste model and parser work.
- Retrying failed documents by default can hide persistent parser or source
  errors.

## Update rules

Update this file when discovery scope, hashing rules, duplicate/version
behavior, or retry rules change.
