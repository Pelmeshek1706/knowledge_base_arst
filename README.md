# personal_kb

## Overview

`personal_kb` is a planned local-first GraphRAG knowledge base for personal and work documents. The intended system ingests local files, stores processed JSON as rebuildable state, syncs a Neo4j graph and vector index, and exposes search and source-grounded Q&A through a CLI and a LangGraph agent.

Current repository status:

- This repository is still a roadmap and implementation workspace, but the
  Phase 0 bootstrap scaffold is now checked in.
- The authoritative project package name in the docs is `personal_kb`.
- `pyproject.toml` uses the project name `personal-kb` and installs the `kb` console script.
- `README.md` documents the current bootstrap scaffold and the remaining
  roadmap work.
- The CLI commands described below are planned MVP commands, not currently implemented unless noted otherwise.

Use this README as the starting point before development, then follow the focused source-of-truth docs under [`docs/`](docs/index.md).

## What This Project Does

The planned MVP will:

- read local documents from `data/`;
- support PDF, DOCX, Markdown, TXT, and XLSX files;
- compute raw file hashes and extracted text hashes for change detection;
- parse and normalize document content;
- chunk documents in a format-aware way;
- generate summaries, tags, entities, and embeddings using local models;
- persist processed output in `kb_storage/`;
- sync documents, chunks, tags, entities, document types, duplicates, versions, and vectors into Neo4j;
- run hybrid retrieval over graph, keyword, tag, entity, vector, and reranker signals;
- answer questions only from retrieved source chunks;
- expose search and Q&A through an `argparse` CLI;
- expose the same search and Q&A capabilities to a LangGraph agent through LangChain `StructuredTool` wrappers.

Current implementation note: the repository already includes the planned
`personal_kb/` source package, test suite, `kb` console script, `.env.example`,
and `configs/default.yaml` scaffold.

## MVP Scope

The MVP includes:

- local file ingestion from `data/`;
- `kb_storage/` as the primary processed JSON store;
- Neo4j graph and vector indexes;
- local LM Studio OpenAI-compatible LLM endpoint for extraction and answer generation;
- local Qwen embedding and reranking models through `transformers` or `sentence-transformers`;
- `argparse` CLI commands for setup, ingestion, search, Q&A, related documents, duplicates, status, and evaluation;
- LangGraph internal agent orchestration;
- LangChain `StructuredTool` wrappers over a service facade;
- benchmark-driven validation with 15-20 initial benchmark cases.

## Non-Goals

The MVP does not include:

- real-time sync with Confluence, Jira, Gmail, Google Drive, or Notion;
- MCP as the primary internal runtime path;
- external write actions;
- file moving, renaming, or deletion;
- OCR for scanned PDFs;
- FAQ or Q&A memory;
- LLM-inferred relationships as required graph behavior;
- web UI;
- Telegram bot;
- production multi-user permissions;
- production-grade observability;
- APOC dependency for Neo4j setup.

## Architecture Summary

The intended architecture has two main paths.

Ingestion path:

```text
Local files in data/
-> deterministic ingestion pipeline
-> processed JSON in kb_storage/
-> GraphSyncService
-> Neo4j graph + vector index
```

Search and Q&A path:

```text
User
-> CLI or LangGraph personal_kb agent
-> LangChain StructuredTools
-> KnowledgeToolService
-> RetrievalService / QAService / GraphService
-> Neo4j + kb_storage + local models
```

The main design rule is:

```text
Framework adapters depend on services.
Services depend on repositories, clients, schemas, and core modules.
Core modules and schemas do not depend on framework adapters.
```

Business logic should live in plain Python services, not in CLI handlers, LangChain tools, LangGraph nodes, or future MCP adapters.

More detail:

- [Architecture overview](docs/architecture/overview.md)
- [Repository structure overview](docs/implementation/repository-structure/overview.md)
- [Package boundaries and import rules](docs/implementation/repository-structure/package-boundaries-and-import-rules.md)
- [Agent design](docs/architecture/agent-design.md)

## Repository Structure

Current top-level repository shape:

```text
.
  AGENTS.md
  README.md
  pyproject.toml
  uv.lock
  env_sample
  data/
  docs/
    architecture/
    implementation/
    product-requirements/
    roadmap/
  *.md legacy snapshot documents
```

Planned implementation structure:

```text
personal_kb/
  cli/
  core/
  schemas/
  storage/
  parsers/
  chunking/
  models/
  ingestion/
  graph/
  retrieval/
  qa/
  tools/
  agent/
  adapters/
  evaluation/
  utils/

tests/
  unit/
  integration/
  fixtures/

benchmark/
kb_storage/
scripts/
configs/
```

Runtime directories:

- `data/`: local source documents. Treat files as read-only inputs.
- `kb_storage/`: processed JSON, manifest, logs, and evaluation reports. This is planned as rebuildable source state for Neo4j.
- `benchmark/`: retrieval and Q&A benchmark cases.

Documentation directories:

- `docs/architecture/`: architecture source of truth.
- `docs/implementation/`: implementation contracts, class design, repository structure, and tool contracts.
- `docs/product-requirements/`: product scope, functional requirements, acceptance criteria, and risks.
- `docs/roadmap/`: phase-by-phase MVP implementation plan.

Top-level versioned Markdown files are legacy snapshots. Prefer the focused files under `docs/`.

## Requirements

Minimum local requirements:

- Python 3.11
- `uv`
- Neo4j 5 or 6 available at `bolt://localhost:7687`
- LM Studio or another OpenAI-compatible local endpoint at `http://localhost:1234/v1`

Planned model defaults from the architecture docs:

- LLM: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- Embeddings: `Qwen/Qwen3-Embedding-0.6B`
- Embedding dimension: `1024`
- Reranker: `Qwen/Qwen3-Reranker-0.6B`
- Neo4j database: `knowledge_base3`, with fallback to `neo4j`

Current dependency note: `pyproject.toml` currently declares only a small dependency set for LangChain, LangGraph, Neo4j, OpenAI, and dotenv. Parser, model, test, lint, and type-check dependencies are expected to be added during implementation.

## Setup

From the repository root:

```bash
uv sync
```

Create a local environment file:

```bash
cp .env.example .env
```

`.env.example` is the current environment template.

Create planned runtime folders if they are missing:

```bash
mkdir -p data kb_storage benchmark
```

Start Neo4j locally before graph setup or integration tests. One possible Docker command is:

```bash
docker run --name personal-kb-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/change-me neo4j:5
```

Start LM Studio in OpenAI-compatible server mode before running extraction, embedding, reranking, or Q&A flows.

## Configuration

The planned MVP configuration should cover:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=change-me
NEO4J_DATABASE=knowledge_base3
NEO4J_FALLBACK_DATABASE=neo4j

LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=mlx-community/Qwen3.5-9B-OptiQ-4bit

PERSONAL_KB_CONFIG=configs/default.yaml
```

Current mismatch to resolve during bootstrap:

- `env_sample` uses legacy names such as `NEO4J_USER`, `LMSTUDIO_URL`, and `LMSTUDIO_MODEL`.
- The focused architecture docs use `NEO4J_USERNAME`, `LM_STUDIO_BASE_URL`, and `LM_STUDIO_MODEL`.
- `configs/default.yaml` and `.env.example` are now part of the checked-in
  bootstrap scaffold, and `env_sample` remains the legacy template to reconcile.

Do not commit `.env`, real credentials, source documents, generated `kb_storage/` content, or local Neo4j volumes.

## CLI Usage

Planned console script:

```toml
[project.scripts]
kb = "personal_kb.cli.main:main"
```

Planned commands:

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

Expected behavior:

- readable output by default;
- `--json` for machine-readable output;
- CLI handlers parse arguments and call services/tools only;
- no business logic in CLI handlers.

Before the console script exists, the bootstrap validation command should be:

```bash
uv run python -m personal_kb.cli.main --help
```

This command is expected to fail until the `personal_kb/` package is created.

## Development Workflow

Recommended first development sequence:

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`docs/index.md`](docs/index.md).
3. Read [`docs/architecture/overview.md`](docs/architecture/overview.md).
4. Read [`docs/implementation/repository-structure/index.md`](docs/implementation/repository-structure/index.md).
5. Read the focused roadmap phase for the task.
6. Implement only the layer needed for the current phase.
7. Add focused tests for new behavior.
8. Update the focused documentation file when behavior, contracts, or structure changes.

Implementation rules:

- Use Python 3.11.
- Use `uv` for dependency management.
- Use Pydantic schemas for shared contracts.
- Keep service logic framework-independent.
- Keep CLI, LangChain, LangGraph, and future MCP adapters thin.
- Store source paths relative to the configured document root where possible.
- Treat original files in `data/` as immutable inputs.
- Keep `kb_storage/` rebuildable and local.

Useful validation commands during implementation:

```bash
uv run pytest -q
uv run pytest tests/<relevant_test_file>.py -q
uv run ruff check .
uv run mypy personal_kb
uv run python -m personal_kb.cli.main --help
```

Some of these commands are TODO until the package, tests, Ruff, and mypy configuration are added.

## Testing and Validation

Use pytest for automated tests.

Planned unit test areas:

- hashing;
- normalization;
- config loading;
- manifest store;
- processed document store;
- parser behavior;
- chunking;
- search plan creation;
- scoring;
- tool facade behavior.

Planned integration test areas:

- Neo4j schema setup;
- graph sync;
- TXT and Markdown ingestion;
- PDF, DOCX, and XLSX parsing;
- retrieval;
- source-grounded Q&A;
- CLI output behavior.

Integration tests may require:

- a running Neo4j instance;
- local LM Studio endpoint;
- local embedding and reranker models.

Benchmark validation is planned under `benchmark/` with 15-20 initial cases. MVP release requires search and Q&A behavior to be evaluated against those cases.

## Documentation Map

Start here:

- [Documentation index](docs/index.md)
- [Architecture index](docs/architecture/index.md)
- [Implementation index](docs/implementation/index.md)
- [Repository structure index](docs/implementation/repository-structure/index.md)
- [Product requirements index](docs/product-requirements/index.md)
- [Roadmap index](docs/roadmap/index.md)

Important focused docs:

- [Architecture overview](docs/architecture/overview.md)
- [Storage design](docs/architecture/storage-design.md)
- [Graph schema](docs/architecture/graph-schema.md)
- [Model strategy](docs/architecture/model-strategy.md)
- [Retrieval design](docs/architecture/retrieval-design.md)
- [Q&A design](docs/architecture/qa-design.md)
- [Agent design](docs/architecture/agent-design.md)
- [Package boundaries and import rules](docs/implementation/repository-structure/package-boundaries-and-import-rules.md)
- [CLI, evaluation, scripts, and tests](docs/implementation/repository-structure/cli-evaluation-scripts-tests.md)
- [MVP implementation order](docs/implementation/repository-structure/mvp-implementation-order.md)

## Agentic Development Workflow

For coding agents and future maintainers:

- Start with `AGENTS.md` for repository guidelines.
- Use the focused docs under `docs/` as the source of truth.
- Do not update legacy top-level snapshot files unless explicitly asked.
- Keep tool wrappers thin.
- Route LangChain StructuredTools through `KnowledgeToolService`.
- Keep LangGraph nodes orchestration-only.
- Do not expose ingestion, setup, rebuild, source mutation, or destructive operations to the MVP agent.
- Do not add MCP as the primary internal path before the core tools are stable.
- Update docs when contracts, command names, package boundaries, config keys, or roadmap status change.

The MVP agent should only have search and Q&A capabilities.

## Current Roadmap

The roadmap is documented in [`docs/roadmap/index.md`](docs/roadmap/index.md).

Phase order:

1. Project bootstrap.
2. Schemas, config, and manifest.
3. Local discovery and hashing.
4. Parsers and normalization.
5. Chunking and processed JSON.
6. Local model clients.
7. Extraction and embeddings.
8. Neo4j setup and graph sync.
9. Retrieval core.
10. Q&A service.
11. `KnowledgeToolService` and StructuredTools.
12. LangGraph agent.
13. CLI integration.
14. Benchmark and evaluation.
15. MVP hardening.

Recommended first sprint target:

```text
schemas + config + manifest + TXT/MD parsing + processed JSON persistence
```

First sprint acceptance criteria:

- User can put TXT and Markdown files into `data/`.
- `kb ingest data` creates `kb_storage/manifest.json` and per-document JSON.
- Re-running ingestion skips unchanged documents.
- Failed files are represented in the manifest.

## Risks / Limitations

Known current limitations:

- `personal_kb/`, `tests/`, `benchmark/`, `kb_storage/`, `configs/`, and
  `.env.example` are part of the bootstrap scaffold; later package layers and
  runtime behavior still need implementation.
- `scripts/` is not yet fully populated for the later roadmap phases.
- `pyproject.toml` project metadata now owns the bootstrap validation stack, but
  later roadmap dependencies still need to be added incrementally.
- `env_sample` reflects a legacy demo configuration and must be reconciled with the MVP configuration contract.
- The current `.gitignore` is minimal and should be expanded before runtime data is generated.
- Neo4j database availability and database-name fallback need validation during implementation.
- Local model output quality, JSON validity, and latency are major MVP risks.
- Retrieval quality must be benchmarked early; it should not be judged only by ad hoc prompts.

## License

No license file is present. Treat the repository as unlicensed until the owner adds an explicit license.
