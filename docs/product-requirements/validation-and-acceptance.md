# Validation and Acceptance

## Purpose

This file defines benchmark data, retrieval metrics, Q&A metrics, system metrics, and MVP acceptance criteria for Personal KB.

## When to read this

Read this when adding tests, defining release gates, evaluating retrieval/Q&A quality, or deciding whether the MVP is accepted.

## Related files

- [Product requirements index](index.md)
- [Overview](overview.md)
- [Users and stories](users-and-stories.md)
- [Functional requirements](functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Release plan](release-plan.md)

## Source of truth

This file is authoritative for Product Requirements validation and acceptance.

## Content

## Benchmark Dataset

Initial benchmark lives in:

```text
benchmark/
```

Initial target size:

```text
15–20 cases
```

Benchmark JSONL example:

```json
{
  "question": "Where is information about accounting budgets?",
  "expected_document_ids": ["doc_123"],
  "expected_answer_contains": ["budget", "accounting"],
  "expected_entities": ["Budget", "Accounting"],
  "expected_source_refs": [
    {
      "file_path": "data/budget_2025.xlsx",
      "sheet": "Budget"
    }
  ]
}
```

## Retrieval Metrics

- Recall@K
- Precision@K
- MRR
- Hit Rate
- nDCG@K

## Q&A Metrics

- answer relevance
- faithfulness
- citation/source correctness
- expected answer coverage
- hallucination rate

## System Metrics

- ingestion latency per document
- search latency
- Q&A latency
- graph sync success rate
- failed extraction rate
- invalid JSON rate

## MVP Acceptance Criteria

The MVP is accepted when:

1. `kb setup-db` creates required Neo4j constraints/indexes/vector index without APOC.
2. `kb ingest data` processes supported files into `kb_storage/`.
3. `kb ingest data` syncs processed documents to Neo4j automatically.
4. Exact duplicates are represented as separate `Document` nodes connected by `DUPLICATE_OF`.
5. Changed files are represented as new `Document` nodes connected by `NEWER_VERSION_OF`.
6. Search returns expected document in top-10 for benchmark questions.
7. Q&A returns source-grounded answers with source references.
8. Search/Q&A CLI output supports readable and `--json` modes.
9. Failed files remain visible in manifest with error state.
10. Neo4j can be rebuilt from processed JSON without re-running expensive model calls.

## Dependencies

- `benchmark/`
- `kb setup-db`
- `kb ingest data`
- `kb search`
- `kb ask`
- `kb_storage/`
- Neo4j constraints, indexes, and vector index
- Processed JSON rebuild flow

## Failure modes / risks

- Missing benchmark cases makes retrieval and Q&A quality unmeasurable.
- Q&A hallucination rate must be tracked because answers must be source-grounded.
- Invalid JSON from local model output can block processing or corrupt downstream data.
- Failed extraction must remain visible instead of disappearing silently.

## Validation

- Run benchmark cases from `benchmark/`.
- Measure retrieval, Q&A, and system metrics.
- Check every MVP acceptance criterion before calling the MVP complete.
- Verify Neo4j rebuild works from processed JSON without expensive model calls.

## Update rules

- Update this file when benchmark format, metrics, or MVP acceptance criteria change.
- Update [release-plan.md](release-plan.md) when acceptance changes alter milestone exit criteria.
- Update focused requirement files when validation reveals missing or changed product behavior.
