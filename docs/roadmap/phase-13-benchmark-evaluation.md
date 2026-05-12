# Phase 13: Benchmark + Evaluation

## Purpose

Validate retrieval and Q&A quality with a small controlled benchmark.

## Status

Draft roadmap phase. Priority: P1.

## Depends on

- [Phase 12: CLI Integration](phase-12-cli-integration.md)

## Outputs

```text
benchmark/
  benchmark.jsonl

personal_kb/evaluation/
  benchmark_loader.py
  retrieval_metrics.py
  qa_metrics.py
  run_benchmark.py
```

## In scope

- Initial benchmark of 15-20 cases.
- Benchmark JSONL file.
- Benchmark loader.
- Retrieval metrics.
- Q&A metrics.
- Benchmark runner.
- Inspectable failures by query, returned documents, scores, and chunks.

## Out of scope

- Large-scale evaluation suites.
- Release hardening beyond benchmark-driven quality checks.

## Related docs

- [Roadmap index](index.md)
- [Product validation and acceptance](../product-requirements/validation-and-acceptance.md)
- [Phase 14: MVP Hardening](phase-14-mvp-hardening.md)

## Source of truth

This file is authoritative for Phase 13 benchmark, metrics, and evaluation
roadmap scope.

## Implementation checklist

Benchmark size:

Initial benchmark: 15-20 cases.

Benchmark item example:

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

Metrics:

| Metric | Purpose |
|---|---|
| Recall@K | expected document appears in top K |
| Precision@K | top K result quality |
| MRR | rank quality |
| nDCG@K | graded ranking quality |
| answer relevance | answer matches expected content |
| faithfulness | answer is supported by chunks |
| source correctness | returned source refs are correct |
| search latency | target near 10 seconds for lookup |

## Exit criteria

- Benchmark can be run from CLI.
- Expected document appears in top-10 for most benchmark cases.
- Q&A returns source-grounded answers.
- Failures are inspectable by query, returned documents, scores, and chunks.

## Validation

- Run the benchmark from CLI.
- Confirm expected documents appear in top-10 for most cases.
- Confirm Q&A answers are source-grounded.
- Inspect failures by query, returned documents, scores, and chunks.
- Track search latency against the target near 10 seconds for lookup.

## Failure modes / risks

- Poor retrieval quality is a high-risk release blocker.
- Uninspectable failures make tuning `SearchPlan` and scoring difficult.
- Source correctness and faithfulness must be measured, not assumed.

## Update rules

Update this file when benchmark size, benchmark schema, metrics, quality gates,
or failure inspection requirements change.
