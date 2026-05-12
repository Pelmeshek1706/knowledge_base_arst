# Project Root And Runtime Data

## Purpose

This file defines top-level repository files, runtime data directories, documentation folders, benchmark data, and `.gitignore` expectations.

## When to read this

Read this when changing root project files, config paths, runtime storage, benchmark files, documentation folder placement, or Git ignore rules.

## Related files

- [overview.md](overview.md)
- [cli-evaluation-scripts-tests.md](cli-evaluation-scripts-tests.md)
- [../../index.md](../../index.md)
- [../../roadmap/index.md](../../roadmap/index.md)

## Source of truth

This file is authoritative for project-root and runtime-data filesystem responsibilities. Package-internal module responsibilities are owned by the other focused repository-structure files.

## Content

### `README.md`

Purpose:

- explains what the project does;
- shows quickstart commands;
- links architecture documents;
- explains MVP limitations.

Should include:

```bash
uv sync
cp .env.example .env
kb setup-db
kb ingest data
kb search "budget accounting"
kb ask "Where is WP2 described?"
```

### `pyproject.toml`

Purpose:

- package metadata;
- runtime dependencies;
- dev dependencies;
- console script definition;
- formatter/linter/test config.

Required console script:

```toml
[project.scripts]
kb = "personal_kb.cli.main:main"
```

Expected dependency groups:

```text
runtime:
- pydantic
- pydantic-settings
- neo4j
- pyyaml
- python-dotenv
- pdfplumber
- pymupdf
- mammoth
- python-docx
- openpyxl
- beautifulsoup4
- markdown
- transformers
- sentence-transformers
- torch
- langchain-core
- langchain
- langgraph

dev:
- pytest
- pytest-cov
- ruff
- mypy
```

MCP dependencies should be optional until the MCP adapter is implemented.

### `.python-version`

Purpose:

- pins local Python version.

Content:

```text
3.11
```

### `.env.example`

Purpose:

- documents environment variables without exposing secrets.

Example:

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

### `configs/`

The original repository layout reserves:

```text
configs/
  default.yaml
  local.example.yaml
  logging.yaml
```

`PERSONAL_KB_CONFIG` points to `configs/default.yaml` by default.

### `data/`

Purpose:

- default local document input folder.

Contains user documents for MVP:

```text
.pdf
.docx
.md
.txt
.xlsx
```

Rules:

- source files are read-only inputs;
- ingestion must not move, rename, or delete files;
- paths stored in JSON should be relative to the project root or configured documents root.

Should be excluded from Git except `.gitkeep`.

### `kb_storage/`

Purpose:

- primary processed storage;
- source of truth for rebuilding Neo4j;
- should not be confused with Neo4j internal data directory.

Expected runtime structure:

```text
kb_storage/
  manifest.json
  documents/
    <document_id>.json
  logs/
    ingestion.log
    search.log
  reports/
    evaluation_<timestamp>.json
```

Rules:

- should be excluded from Git except `.gitkeep`;
- per-document JSON stores raw extracted text, chunks, summaries, tags, entities, embeddings, relationships, and processing metadata;
- Neo4j can be rebuilt from this folder without re-running parsing/LLM extraction/embedding generation.

### `benchmark/`

Purpose:

- stores evaluation cases.

Expected structure:

```text
benchmark/
  README.md
  questions.jsonl
  expected_documents.jsonl
  expected_answers.jsonl
```

Initial benchmark target:

```text
15-20 cases
```

### `docs/architecture/`

Purpose:

- stores stable design documents.

Original expected documents:

```text
Technical_Architecture_Personal_KB_v0.3.md
Product_Requirements_Document_Personal_KB_v0.2.md
Neo4j_Graph_Schema_Personal_KB_v0.1.md
Python_Class_Design_Personal_KB_v0.1.md
MCP_Tool_Contracts_Personal_KB_v0.3.md
Implementation_Roadmap_Personal_KB_v0.1.md
Repository_Structure_Personal_KB_v0.1.md
```

Rules:

- update the relevant architecture document before making large implementation changes;
- do not let code drift away from schemas/tool contracts;
- if a service signature changes, update `Python_Class_Design` and `MCP_Tool_Contracts`.

Conflict / Review needed:

The original expected document list is outdated relative to the current focused documentation model. In the current model, use [../../index.md](../../index.md) and the focused indexes under `docs/architecture/`, `docs/implementation/`, `docs/roadmap/`, and `docs/product-requirements/`.

### `docs/diagrams/`

Purpose:

- stores visual architecture and flow diagrams.

Expected diagrams:

```text
component_diagram.svg
ingestion_activity.svg
search_activity.svg
ingestion_sequence.svg
graph_schema.svg
```

### Recommended `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Environments
.venv/
.env

# Runtime data
data/*
!data/.gitkeep
kb_storage/*
!kb_storage/.gitkeep

# Local config
configs/local.yaml

# Neo4j local volumes, if created later
neo4j/data/
neo4j/logs/
neo4j/import/
neo4j/plugins/

# OS
.DS_Store
```

## Dependencies

- `pyproject.toml`
- `.python-version`
- `.env.example`
- `configs/default.yaml`
- `data/`
- `kb_storage/`
- `benchmark/`
- `docs/`

## Failure modes / risks

- Secrets can leak if `.env` is committed.
- Source documents can be corrupted if ingestion mutates `data/`.
- Neo4j rebuild assumptions break if `kb_storage/` is not treated as the processed source of truth.
- Documentation can drift if obsolete versioned documents are updated instead of focused documentation files.

## Validation

- `uv sync` should install project dependencies.
- `cp .env.example .env` should create a local config starting point.
- `kb setup-db`, `kb ingest data`, `kb search`, and `kb ask` should remain valid quickstart commands.
- `data/*`, `kb_storage/*`, `.env`, and `configs/local.yaml` should be ignored by Git except required `.gitkeep` files.

## Update rules

Update this file when root files, config files, runtime folders, documentation folder ownership, benchmark data paths, quickstart commands, or ignore rules change.
