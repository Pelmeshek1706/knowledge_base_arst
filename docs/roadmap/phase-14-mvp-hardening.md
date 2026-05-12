# Phase 14: MVP Hardening

## Purpose

Make the MVP stable enough for iterative use on a local document folder.

## Status

Draft roadmap phase. Priority: P1.

## Depends on

- [Phase 13: Benchmark + Evaluation](phase-13-benchmark-evaluation.md)

## Outputs

- Error handling improvements.
- Structured logs.
- Config validation.
- README usage guide.
- Minimal troubleshooting guide.
- Regression tests for ingestion/retrieval.

## In scope

- Error handling.
- Structured logs.
- Config validation.
- README usage guide.
- Minimal troubleshooting guide.
- Regression tests for ingestion and retrieval.
- Graceful degradation for failed documents, Neo4j downtime, and unavailable
  reranker.

## Out of scope

- Post-MVP MCP adapter.
- External source connectors.
- FAQ/QA memory.
- Web UI.
- Telegram bot.
- OCR.
- Access control.

## Related docs

- [Roadmap index](index.md)
- [Product risks and future requirements](../product-requirements/risks-and-future-requirements.md)
- [Product validation and acceptance](../product-requirements/validation-and-acceptance.md)

## Source of truth

This file is authoritative for Phase 14 MVP hardening roadmap scope.

## Implementation checklist

1. Improve error handling.
2. Add structured logs.
3. Validate config.
4. Write README usage guide.
5. Write minimal troubleshooting guide.
6. Add regression tests for ingestion/retrieval.

## Exit criteria

- Failed documents do not break full ingestion.
- Neo4j downtime does not destroy processed JSON state.
- Search degrades gracefully if reranker is unavailable.
- Logs do not dump full document text by default.
- System can be run repeatedly without corrupting manifest or graph state.

## Validation

- Ingest a folder containing failing documents and confirm full ingestion
  continues.
- Simulate Neo4j downtime and confirm processed JSON state is preserved.
- Disable reranker and confirm search degrades gracefully.
- Review logs and confirm full document text is not dumped by default.
- Run repeated ingestion and sync cycles and confirm manifest and graph state
  remain valid.

## Failure modes / risks

- Failed documents must not break full ingestion.
- Neo4j downtime must not destroy processed JSON state.
- Logs must not dump full document text by default.
- Repeated runs must not corrupt manifest or graph state.

## Update rules

Update this file when hardening outputs, troubleshooting requirements,
regression coverage, or MVP stability criteria change.
