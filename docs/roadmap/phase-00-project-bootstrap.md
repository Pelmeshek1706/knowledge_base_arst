# Phase 0: Project Bootstrap

## Purpose

Create the minimum repository structure required to develop the project
without mixing business logic, adapters, and infrastructure.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- None.

## Outputs

```text
personal_kb/
  __init__.py
  cli/
  core/
  schemas/
  storage/
  parsers/
  ingestion/
  models/
  graph/
  retrieval/
  qa/
  tools/
  agent/
  evaluation/
configs/
  config.yaml
benchmark/
data/
kb_storage/
tests/
pyproject.toml
README.md
```

## In scope

- Initialize project with `uv`.
- Set Python version to 3.11.
- Add base dependencies.
- Add package entrypoint for `kb` CLI.
- Add `.env.example` for Neo4j and LM Studio settings.

Base dependencies:

- `pydantic`
- `pyyaml`
- `neo4j`
- `pdfplumber`
- `pymupdf`
- `mammoth`
- `python-docx`
- `openpyxl`
- `transformers`
- `sentence-transformers`
- `langchain`
- `langgraph`
- `pytest`

## Out of scope

- Neo4j setup.
- Model loading.
- File parsing or processing.
- Import-time side effects.
- Later roadmap phases listed in [the roadmap index](index.md).

## Related docs

- [Roadmap index](index.md)
- [Implementation index](../implementation/index.md)
- [Architecture overview](../architecture/overview.md)

## Source of truth

This file is authoritative for Phase 0 bootstrap scope, outputs, and exit
criteria.

## Implementation checklist

1. Initialize project with `uv`.
2. Set Python version to 3.11.
3. Add the base dependency set listed above.
4. Add package entrypoint for `kb` CLI.
5. Add `.env.example` for Neo4j and LM Studio settings.

## Exit criteria

- `uv sync` works.
- `python -m personal_kb.cli.main --help` works.
- Empty package imports without side effects.
- No Neo4j, model, or file processing is triggered during import.

## Validation

- Run `uv sync`.
- Run `python -m personal_kb.cli.main --help`.
- Import the package in a clean Python process and confirm no Neo4j, model, or
  file processing is triggered.

## Failure modes / risks

- Mixing business logic, adapters, and infrastructure too early creates
  expensive refactors in later phases.
- Import-time side effects can trigger Neo4j, model, or file processing before
  configuration is ready.

## Update rules

Update this file when bootstrap structure, base dependencies, CLI entrypoint
requirements, or import-safety criteria change.
