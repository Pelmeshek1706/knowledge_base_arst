# Repository Structure Index

## Purpose

This folder defines the repository structure for the `personal_kb` project: root files, runtime data directories, package layout, dependency boundaries, implementation order, validation surfaces, and reserved future extension locations.

## When to read this

Start here for:

- repository layout changes;
- package or module ownership changes;
- implementation planning that depends on file locations;
- import boundary or dependency direction changes;
- runtime data, `kb_storage/`, benchmark, or `.gitignore` changes;
- CLI, script, test, or evaluation layout changes;
- future adapter or connector placement decisions.

## Source of truth

| Topic | Authoritative file |
|---|---|
| High-level repository layout, status, MVP flow, and final repository rule | [overview.md](overview.md) |
| Root files, config files, runtime data directories, documentation folders, and `.gitignore` | [project-root-and-runtime-data.md](project-root-and-runtime-data.md) |
| Package dependency direction, layer boundaries, and import rules | [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md) |
| `personal_kb/core/`, `personal_kb/schemas/`, and `personal_kb/storage/` | [core-schemas-storage.md](core-schemas-storage.md) |
| Parsers, chunkers, local model clients, and ingestion pipeline | [ingestion-parsing-models.md](ingestion-parsing-models.md) |
| Neo4j graph layer, retrieval, scoring, reranking, and grounded Q&A | [graph-retrieval-qa.md](graph-retrieval-qa.md) |
| Tool facade, LangChain StructuredTools, LangGraph agent, and framework adapters | [tools-agent-adapters.md](tools-agent-adapters.md) |
| Evaluation modules, CLI commands, developer scripts, and tests | [cli-evaluation-scripts-tests.md](cli-evaluation-scripts-tests.md) |
| MVP implementation order by repository area | [mvp-implementation-order.md](mvp-implementation-order.md) |
| Reserved future MCP, API, connector, and memory extensions | [future-extensions.md](future-extensions.md) |

## Reading order

1. Read [overview.md](overview.md) for the repository summary and main design rule.
2. Read the focused file related to the current task.
3. Read related files listed in the focused document.
4. Do not scan the whole folder unless explicitly requested.

## Files

| Topic | File | Purpose |
|---|---|---|
| Overview | [overview.md](overview.md) | Explains the project status, high-level repository tree, MVP flow, and final recommendation. |
| Project root and runtime data | [project-root-and-runtime-data.md](project-root-and-runtime-data.md) | Defines top-level files, runtime directories, docs folders, benchmark data, and `.gitignore` rules. |
| Package boundaries and imports | [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md) | Defines allowed dependency direction and forbidden imports. |
| Core, schemas, storage | [core-schemas-storage.md](core-schemas-storage.md) | Defines foundation modules, shared Pydantic contracts, manifest storage, and processed JSON storage. |
| Ingestion, parsing, models | [ingestion-parsing-models.md](ingestion-parsing-models.md) | Defines parsers, chunking, local model clients, and deterministic ingestion services. |
| Graph, retrieval, Q&A | [graph-retrieval-qa.md](graph-retrieval-qa.md) | Defines Neo4j setup/sync, hybrid retrieval, scoring, reranking, and grounded answer generation. |
| Tools, agent, adapters | [tools-agent-adapters.md](tools-agent-adapters.md) | Defines the tool facade, StructuredTool wrappers, LangGraph state/nodes, and adapter boundaries. |
| CLI, evaluation, scripts, tests | [cli-evaluation-scripts-tests.md](cli-evaluation-scripts-tests.md) | Defines command layout, evaluation metrics, scripts, and unit/integration test areas. |
| MVP implementation order | [mvp-implementation-order.md](mvp-implementation-order.md) | Preserves sprint-by-sprint repository implementation order and acceptance checks. |
| Future extensions | [future-extensions.md](future-extensions.md) | Preserves reserved non-MVP extension locations and constraints. |

## Update rules

- Update [overview.md](overview.md) when the high-level repository tree or main design rule changes.
- Update [project-root-and-runtime-data.md](project-root-and-runtime-data.md) when root files, runtime folders, docs folders, benchmark data, config files, or `.gitignore` rules change.
- Update [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md) when dependency direction or import constraints change.
- Update the focused package-area file when files are added, removed, renamed, or their responsibility changes.
- Update [mvp-implementation-order.md](mvp-implementation-order.md) when repository implementation sequence or acceptance checks change.
- Update [future-extensions.md](future-extensions.md) before adding a reserved adapter, connector, API, or memory package.
- Update [../index.md](../index.md) when this folder is added, removed, or materially reorganized.

## Do not read everything by default

Coding agents should open only the focused files needed for the current task. Use this index as the router.
