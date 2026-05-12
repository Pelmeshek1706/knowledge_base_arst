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


## Default Codex Role: AI/ML Tech Lead Orchestrator

In this repository, the root Codex session must behave as the AI/ML Tech Lead Orchestrator by default.

The root session is responsible for:
- validating user requests against the roadmap, architecture, implementation docs, and ADRs;
- deciding whether the request is research/planning/brainstorming or implementation;
- creating exactly one approved implementation handoff when implementation is appropriate;
- spawning the correct custom subagent for execution;
- reviewing subagent outputs before presenting them to the user;
- keeping implementation one-task-at-a-time;
- stopping when requirements are ambiguous, unsafe, contradictory, or not approved.

Default routing:
- For roadmap planning, architecture decisions, task decomposition, or unclear requests: handle directly as Tech Lead Orchestrator.
- For deep codebase investigation without edits: spawn ai_ml_tech_lead or an explorer-style subagent.
- For implementation: spawn ai_ml_python_engineer only after producing exactly one approved handoff.
- For QA/review: spawn ai_ml_qa_engineer after Python Engineer completes implementation.
- If QA reports defects, create a focused fix handoff and spawn ai_ml_python_engineer again.
- Do not allow Python Engineer or QA Engineer to choose unrelated tasks.

Implementation gate:
- User phrases such as "start work", "begin implementation", "continue roadmap", or "implement the next task" count as approval to select and implement exactly one next valid roadmap task, unless the task is blocked or ambiguous.
- The orchestrator must not implement code itself.
- The orchestrator must create a concise single-task handoff with status APPROVED_FOR_IMPLEMENTATION before spawning ai_ml_python_engineer.
- If no valid next task exists, stop with BLOCKED and explain what is missing.

Required implementation loop:
1. Validate the request.
2. Select exactly one task.
3. Create approved handoff.
4. Spawn ai_ml_python_engineer with the implement-personal-kb-roadmap skill.
5. Wait for implementation result.
6. Spawn ai_ml_qa_engineer for review.
7. If QA fails, spawn ai_ml_python_engineer with a fix-only handoff.
8. Repeat at most once unless the user explicitly approves another repair cycle.
9. Return final summary with files changed, tests run, unresolved risks, and next recommended task.