# CLI, Evaluation, Scripts, And Tests

## Purpose

This file defines the repository areas for user-facing CLI commands, benchmark evaluation modules, developer scripts, and tests.

## When to read this

Read this when implementing or changing `personal_kb/cli/`, `personal_kb/evaluation/`, `scripts/`, `tests/`, or benchmark validation behavior.

## Related files

- [project-root-and-runtime-data.md](project-root-and-runtime-data.md)
- [mvp-implementation-order.md](mvp-implementation-order.md)
- [graph-retrieval-qa.md](graph-retrieval-qa.md)
- [tools-agent-adapters.md](tools-agent-adapters.md)
- [../../roadmap/index.md](../../roadmap/index.md)

## Source of truth

This file is authoritative for repository structure and responsibilities of CLI, evaluation, scripts, and tests.

## Content

## `personal_kb/evaluation/`

Purpose:

- benchmark retrieval and Q&A;
- prevent subjective evaluation.

### `benchmark_loader.py`

Loads JSONL benchmark cases from `benchmark/`.

### `retrieval_metrics.py`

Implements:

```text
Recall@K
Precision@K
MRR
Hit Rate
nDCG@K
```

### `qa_metrics.py`

Implements or structures manual/LLM-assisted evaluation for:

```text
answer relevance
faithfulness
citation correctness
expected answer coverage
hallucination rate
```

### `evaluator.py`

Runs benchmark end-to-end.

## `personal_kb/cli/`

Purpose:

- user-facing CLI via `argparse`.

### Commands

```bash
kb setup-db
kb ingest data
kb search "accounting budget"
kb ask "Where is WP2 described?"
kb related --doc-id <uuid>
kb duplicates
kb status
kb evaluate
```

### Rules

- CLI handlers parse arguments only;
- CLI handlers call services/tools;
- no business logic in CLI functions;
- readable output by default;
- `--json` for machine-readable output.

## `scripts/`

Purpose:

- developer convenience scripts;
- not core runtime.

Examples:

```text
bootstrap_project.py
run_ingestion.py
run_evaluation.py
export_graph_sample.py
```

Scripts may call package APIs but should not contain implementation logic that is unavailable from the package.

## `tests/`

Purpose:

- verify schemas, storage, ingestion, graph sync, retrieval, and Q&A.

### Unit tests

Examples:

```text
test_hashing.py
test_normalization.py
test_manifest_store.py
test_search_plan.py
test_scoring.py
```

### Integration tests

Examples:

```text
test_neo4j_schema.py
test_graph_sync.py
test_txt_md_ingestion.py
test_search_documents.py
test_answer_question.py
```

Integration tests may require Neo4j.

## Dependencies

- `benchmark/`
- `personal_kb/evaluation/benchmark_loader.py`
- `personal_kb/evaluation/retrieval_metrics.py`
- `personal_kb/evaluation/qa_metrics.py`
- `personal_kb/evaluation/evaluator.py`
- `personal_kb/cli/main.py`
- `personal_kb/cli/commands/`
- `personal_kb/cli/formatters/`
- `scripts/`
- `tests/unit/`
- `tests/integration/`
- `tests/fixtures/`

## Failure modes / risks

- CLI commands can drift into business logic instead of calling services/tools.
- Scripts can become hidden runtime paths that bypass package APIs.
- Evaluation can become subjective if benchmark metrics and diagnostics are not used.
- Integration tests can fail without Neo4j, so Neo4j requirements must be explicit.

## Validation

- `kb status` can load config and initialize/read manifest.
- `kb search "some topic" --json` returns ranked documents with confidence and source refs.
- `kb ask "question about a document" --json` returns answer, source documents, and supporting chunks.
- `kb evaluate` runs benchmark diagnostics.
- Unit tests cover hashing, normalization, manifest store, search plan, and scoring.
- Integration tests cover Neo4j schema, graph sync, TXT/MD ingestion, document search, and question answering.

## Update rules

Update this file when CLI commands, output rules, evaluation metrics, benchmark file locations, developer scripts, test directories, or validation expectations change.
