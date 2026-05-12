# Repository Guidelines

## Project Structure & Module Organization

This repository is the roadmap and implementation workspace for `personal_kb`, a local-first GraphRAG knowledge base using Python, LangGraph, Neo4j, and local model endpoints. Source code should live in `personal_kb/`, with business logic in services and framework adapters kept thin. Follow the focused docs under `docs/architecture/`, `docs/implementation/`, `docs/product-requirements/`, and `docs/roadmap/`; top-level versioned Markdown files are legacy snapshots. Runtime inputs belong in `data/`, processed JSON in `kb_storage/`, benchmarks in `benchmark/`, scripts in `scripts/`, and tests in `tests/unit/`, `tests/integration/`, and `tests/fixtures/`. Visual assets and diagrams belong under `docs/diagrams/` when added.

## Build, Test, and Development Commands

- `uv sync`: install Python 3.11 dependencies from `pyproject.toml` and `uv.lock`.
- `uv run pytest -q`: run the full pytest suite once tests exist.
- `uv run pytest tests/<relevant_test_file>.py -q`: run a narrow test during implementation.
- `uv run ruff check .`: run lint checks when Ruff is configured.
- `uv run mypy personal_kb`: run type checks once the package exists.
- `uv run python -m personal_kb.cli.main --help`: verify the CLI entrypoint after bootstrap.

## Coding Style & Naming Conventions

Use Python 3.11, four-space indentation, type hints for public functions, and Pydantic schemas for shared contracts. Keep dependency direction aligned with `docs/implementation/repository-structure/package-boundaries-and-import-rules.md`: CLI, adapters, and agent code call tools/services; services call storage, graph, retrieval, QA, and model clients; schemas and core modules stay framework-independent. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `test_<behavior>.py` for tests.

## Testing Guidelines

Use pytest. Add focused unit tests beside the affected layer and integration tests for Neo4j, graph sync, ingestion, retrieval, and Q&A behavior. Integration tests may require a running Neo4j instance and local model endpoint; document those requirements in the test or fixture. There is no fixed coverage gate yet, but changes should include tests for new behavior and regressions.

## Commit & Pull Request Guidelines

Git history uses short imperative subjects such as `add langchain tracing` and `update code`; keep that style and keep the first line under 72 characters. Pull requests should describe the roadmap phase or module touched, summarize behavior changes, list validation commands run, and note any Neo4j, model, or config requirements. Include screenshots only for diagram or UI changes.

## Security & Configuration Tips

Do not commit `.env`, real credentials, source documents, generated `kb_storage/` content, or local Neo4j volumes. Use `env_sample` as the current environment template until `.env.example` is added.
