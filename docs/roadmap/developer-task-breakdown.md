# Developer Task Breakdown

Plan Status: `IN_PROGRESS`

## Purpose

This file turns the roadmap and architecture docs into an approval-gated,
one-task-at-a-time implementation backlog for the AI/ML Python Engineer.

Rules for execution:

- Tasks start as `PENDING_USER_APPROVAL` and move forward one at a time.
- Only one task may be handed off at a time after explicit approval.
- After each implementation task, QA must run before the next task starts.
- If a task hits a documented stop condition, the engineer must stop and ask
  the Tech Lead or user rather than inventing project policy.

Allowed task statuses:

- `PENDING_USER_APPROVAL`
- `APPROVED_FOR_IMPLEMENTATION`
- `IN_PROGRESS`
- `READY_FOR_QA`
- `QA_FAILED`
- `QA_PASSED`
- `DONE`

## Current Repo State

- The repository is still docs-first. `personal_kb/` does not exist yet.
- `pyproject.toml` is minimal and does not define the `kb` console script.
- `tests/unit/`, `tests/integration/`, and `tests/fixtures/` do not exist yet.
- `docs/adr/` was requested as input but is missing in the current checkout.
- Several docs disagree on file names and package locations. Those conflicts are
  listed under Open Questions and appear again as task-level stop conditions.

## Sequencing Decision

- Follow the roadmap order from Phase 0 through Phase 14.
- Keep business logic in services, not CLI handlers, tools, or LangGraph nodes.
- Preserve `kb_storage/` as the primary processed source of truth.
- Keep the agent read-only in MVP.
- Favor smaller, composable implementation tasks over broad phase-sized drops.

## Recommended First Task

- `TL-001` is the recommended first task because the repo currently lacks the
  package skeleton, dependency baseline, console entrypoint, and config/env
  scaffolding required by every later phase.

## Execution Order

1. `TL-001`
2. `TL-002`
3. `TL-003`
4. `TL-004`
5. `TL-005`
6. `TL-006`
7. `TL-007`
8. `TL-008`
9. `TL-009`
10. `TL-010`
11. `TL-011`
12. `TL-012`
13. `TL-013`
14. `TL-014`
15. `TL-015`
16. `TL-016`
17. `TL-017`
18. `TL-018`
19. `TL-019`

## Tasks

### Task ID: `TL-001`

- Status: `DONE`
- Title: Project bootstrap and repository scaffolding
- Roadmap Phase(s): Phase 0
- Goal: Create the initial `personal_kb/` package skeleton, baseline project
  directories, console entrypoint, and dependency/config scaffolding without
  adding business logic.
- Context: The current repo has docs, sample data, `env_sample`, and a minimal
  `pyproject.toml`, but no package tree or CLI entrypoint.
- Docs to Read:
  - `AGENTS.md`
  - `docs/roadmap/phase-00-project-bootstrap.md`
  - `docs/architecture/overview.md`
  - `docs/implementation/repository-structure/project-root-and-runtime-data.md`
  - `docs/implementation/repository-structure/package-boundaries-and-import-rules.md`
- Files to Inspect:
  - `pyproject.toml`
  - `README.md`
  - `env_sample`
  - `.python-version`
  - `docs/roadmap/phase-00-project-bootstrap.md`
- Likely Files to Modify:
  - `pyproject.toml`
  - `README.md`
  - `.gitignore`
  - `personal_kb/__init__.py`
  - `personal_kb/cli/main.py`
  - `personal_kb/cli/__init__.py`
  - `configs/`
  - `tests/`
  - `.env.example` or `env_sample` after policy confirmation
- Non-Goals:
  - No ingestion logic
  - No Neo4j setup
  - No model loading
  - No parser, retrieval, tool, or agent business logic
- Implementation Steps:
  1. Add the package skeleton and empty subpackages required by the roadmap.
  2. Expand `pyproject.toml` to include the planned runtime and dev
     dependencies plus the `kb` console script.
  3. Add a minimal `personal_kb.cli.main` entrypoint that exposes `--help`
     without side effects.
  4. Add base runtime directories and placeholder files where the docs require
     them.
  5. Add the approved environment/config template path after resolving the
     `env_sample` versus `.env.example` ambiguity.
- Acceptance Criteria:
  - `uv sync` succeeds.
  - `uv run python -m personal_kb.cli.main --help` succeeds.
  - Importing `personal_kb` causes no Neo4j, model, or file-processing side
    effects.
  - The repo layout matches the agreed bootstrap convention.
- Tests:
  - `uv sync`
  - `uv run python -m personal_kb.cli.main --help`
  - Import smoke check for `personal_kb`
- QA Focus:
  - Package import safety
  - Console script wiring
  - Dependency completeness versus the roadmap
  - Correct ignored/runtime directory setup
- Risks:
  - Locking in the wrong package/file names will create churn in later tasks.
  - Adding import-time side effects will break tests and CLI startup.
- Stop Conditions:
  - If the team must choose between `env_sample` and `.env.example`, stop and
    request direction rather than keeping both with overlapping authority.
  - If the package naming conflict (`agent/` versus `agents/`) must be resolved
    at bootstrap time, stop and escalate.
- Dependencies: None

### Task ID: `TL-002`

- Status: `PENDING_USER_APPROVAL`
- Title: Shared schemas, config, and core utility foundations
- Roadmap Phase(s): Phase 1
- Goal: Implement the typed config, schema, path, hashing, normalization, ID,
  time, and exception foundations used by all later layers.
- Context: Later storage, ingestion, graph, retrieval, and tool layers all
  depend on stable Pydantic contracts and pure utility helpers.
- Docs to Read:
  - `docs/roadmap/phase-01-schemas-config-manifest.md`
  - `docs/implementation/class-design/schemas.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/tool-contracts/knowledge-tool-service.md`
- Files to Inspect:
  - `pyproject.toml`
  - `docs/implementation/class-design/schemas.md`
  - `docs/architecture/model-strategy.md`
  - `docs/implementation/tool-contracts/search-plan.md`
- Likely Files to Modify:
  - `personal_kb/core/config_loader.py`
  - `personal_kb/core/paths.py`
  - `personal_kb/core/hashing.py`
  - `personal_kb/core/normalization.py`
  - `personal_kb/core/errors.py`
  - `personal_kb/core/ids.py`
  - `personal_kb/core/time.py`
  - `personal_kb/schemas/common.py`
  - `personal_kb/schemas/config.py`
  - `personal_kb/schemas/document.py`
  - `personal_kb/schemas/chunk.py`
  - `personal_kb/schemas/entity.py`
  - `personal_kb/schemas/tag.py`
  - `personal_kb/schemas/manifest.py`
  - `personal_kb/schemas/processing.py`
  - `personal_kb/schemas/relationships.py`
  - `personal_kb/schemas/search.py`
  - `personal_kb/schemas/qa.py`
  - `personal_kb/schemas/tools.py`
- Non-Goals:
  - No manifest persistence
  - No file discovery
  - No parsing or chunking
  - No graph sync or retrieval logic
- Implementation Steps:
  1. Define the Pydantic config and shared domain schemas.
  2. Implement config loading with validation and environment-variable support.
  3. Implement project-relative path resolution and traversal protection.
  4. Implement deterministic hashing and label normalization helpers.
  5. Add project-specific exception types used across later services.
- Acceptance Criteria:
  - Representative valid payloads validate successfully.
  - Invalid schema payloads fail clearly.
  - Relative path handling is consistent from project root.
  - No service-facing code still depends on raw dictionaries for shared
    contracts.
- Tests:
  - Unit tests for schema validation
  - Unit tests for path resolution
  - Unit tests for hashing
  - Unit tests for normalization
  - Unit tests for config loading and env overrides
- QA Focus:
  - Schema completeness
  - Validation error clarity
  - Path portability
  - Hashing determinism
- Risks:
  - Schema drift here will ripple through every later task.
  - Mis-modeled search/QA contracts will leak into tools and CLI.
- Stop Conditions:
  - If the docs disagree on config file naming in a way that changes loader
    behavior (`configs/config.yaml` versus `configs/default.yaml`), stop and
    ask for a single source-of-truth path.
- Dependencies:
  - `TL-001`

### Task ID: `TL-003`

- Status: `PENDING_USER_APPROVAL`
- Title: Manifest store and processed document store
- Roadmap Phase(s): Phase 1
- Goal: Implement durable JSON persistence for the manifest and per-document
  processed records, including failed-document handling and atomic writes.
- Context: The architecture treats `kb_storage/` as the primary rebuildable
  processed state; Neo4j is downstream of this layer.
- Docs to Read:
  - `docs/roadmap/phase-01-schemas-config-manifest.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
  - `docs/implementation/repository-structure/core-schemas-storage.md`
- Files to Inspect:
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
  - `docs/roadmap/phase-01-schemas-config-manifest.md`
- Likely Files to Modify:
  - `personal_kb/storage/manifest_store.py`
  - `personal_kb/storage/processed_document_store.py`
  - `personal_kb/storage/json_store.py`
  - `tests/unit/storage/test_manifest_store.py`
  - `tests/unit/storage/test_processed_document_store.py`
  - `tests/fixtures/`
- Non-Goals:
  - No parser or chunker logic
  - No graph sync
  - No retrieval logic
- Implementation Steps:
  1. Implement manifest load/save with atomic writes and typed validation.
  2. Implement manifest lookups by document ID, source path, and hashes.
  3. Implement failed-document persistence with explicit error details.
  4. Implement processed-document JSON save/load/iterate behavior.
  5. Ensure paths stored in JSON remain project-relative.
- Acceptance Criteria:
  - Failed documents remain in the manifest with `status="failed"`.
  - Per-document JSON validates on load.
  - Manifest writes are atomic and human-readable.
  - Full raw text is not stored in the manifest.
- Tests:
  - Unit tests for load/save
  - Unit tests for atomic replace behavior
  - Unit tests for failed-entry persistence
  - Unit tests for processed-document round trips
- QA Focus:
  - Manifest integrity across repeated writes
  - Validation failures on corrupt JSON
  - Correct relative-path handling
- Risks:
  - Incorrect persistence semantics will break rebuildability and retries.
  - Non-atomic writes can corrupt the source of truth.
- Stop Conditions:
  - If the manifest schema needs fields not covered by existing docs, stop and
    escalate instead of improvising new state.
- Dependencies:
  - `TL-002`

### Task ID: `TL-004`

- Status: `PENDING_USER_APPROVAL`
- Title: Local discovery, hashing, duplicate detection, and planning
- Roadmap Phase(s): Phase 2
- Goal: Implement supported-file discovery plus deterministic pre-parse
  processing decisions for skip, new, duplicate, version, and failed-retry
  cases.
- Context: Duplicate/version policy must be decided before expensive parsing or
  model work.
- Docs to Read:
  - `docs/roadmap/phase-02-local-discovery-hashing.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
  - `docs/architecture/overview.md`
- Files to Inspect:
  - `data/`
  - `docs/roadmap/phase-02-local-discovery-hashing.md`
  - `personal_kb/storage/manifest_store.py`
  - `personal_kb/core/hashing.py`
- Likely Files to Modify:
  - `personal_kb/ingestion/file_discovery.py`
  - `personal_kb/ingestion/processing_planner.py`
  - `personal_kb/ingestion/duplicate_detector.py`
  - `tests/unit/ingestion/test_file_discovery.py`
  - `tests/unit/ingestion/test_processing_planner.py`
  - `tests/unit/ingestion/test_duplicate_detector.py`
- Non-Goals:
  - No parser implementation
  - No chunking
  - No model calls
  - No Neo4j writes
- Implementation Steps:
  1. Scan `data/` recursively for supported extensions only.
  2. Compute raw-bytes hashes for candidates.
  3. Compare candidates against manifest state to decide skip/new/duplicate
     version behavior.
  4. Implement retry policy for previously failed entries.
  5. Return typed planning results for later ingestion orchestration.
- Acceptance Criteria:
  - Same-path same-hash files are skipped.
  - Same-path changed files plan `NEWER_VERSION_OF`.
  - Different-path same-hash files plan duplicate handling.
  - Failed entries retry only when allowed by policy.
  - Unsupported file types are ignored.
- Tests:
  - Unit tests for each planning branch
  - Unit tests for supported-extension filtering
  - Unit tests for failed-retry gating
- QA Focus:
  - Duplicate/version correctness
  - Determinism of planning decisions
  - No unnecessary processing of unsupported files
- Risks:
  - Duplicate/version confusion will pollute both JSON and graph state later.
  - Missing pre-parse skip logic will waste model runtime.
- Stop Conditions:
  - If the duplicate canonicalization rule must change beyond current docs,
    stop and ask before implementing a new policy.
- Dependencies:
  - `TL-003`

### Task ID: `TL-005`

- Status: `PENDING_USER_APPROVAL`
- Title: TXT and Markdown parsing plus first chunking slice
- Roadmap Phase(s): Phases 3-4
- Goal: Implement the simplest supported file types first: TXT and Markdown
  parsing, source-reference preservation, and initial chunking behavior.
- Context: The roadmap explicitly recommends starting with TXT/MD before more
  complex formats.
- Docs to Read:
  - `docs/roadmap/phase-03-parsers-normalization.md`
  - `docs/roadmap/phase-04-chunking-processed-json.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
  - `docs/implementation/repository-structure/ingestion-parsing-models.md`
- Files to Inspect:
  - `docs/roadmap/phase-03-parsers-normalization.md`
  - `docs/roadmap/phase-04-chunking-processed-json.md`
  - sample text/markdown inputs under `data/`
- Likely Files to Modify:
  - `personal_kb/parsers/base.py`
  - `personal_kb/parsers/txt_parser.py`
  - `personal_kb/parsers/markdown_parser.py`
  - `personal_kb/parsers/registry.py`
  - `personal_kb/chunking/base.py`
  - `personal_kb/chunking/txt_chunker.py`
  - `personal_kb/chunking/markdown_chunker.py`
  - `personal_kb/chunking/registry.py`
  - `tests/unit/parsers/test_txt_parser.py`
  - `tests/unit/parsers/test_markdown_parser.py`
  - `tests/unit/chunking/test_txt_chunker.py`
  - `tests/unit/chunking/test_markdown_chunker.py`
- Non-Goals:
  - No PDF/DOCX/XLSX support
  - No model extraction
  - No graph sync
- Implementation Steps:
  1. Define parser and chunker interfaces plus registries.
  2. Implement TXT parsing with whitespace normalization.
  3. Implement Markdown parsing with heading preservation.
  4. Implement TXT fixed-size chunking.
  5. Implement Markdown heading-aware chunking with usable source refs.
- Acceptance Criteria:
  - TXT and Markdown files parse successfully into typed parsed documents.
  - Chunking produces stable chunk ordering and usable source refs.
  - Registry lookup resolves `.txt` and `.md` cleanly.
- Tests:
  - Unit tests for TXT and Markdown parsing
  - Unit tests for registry mappings
  - Unit tests for chunk boundary behavior
- QA Focus:
  - Heading preservation
  - Chunk-source references
  - Stable chunk ordering
- Risks:
  - Weak source refs here will reduce later citation quality.
  - Early registry mistakes will complicate advanced parser work.
- Stop Conditions:
  - If the team wants to collapse chunking into `ingestion/chunking_service.py`
    instead of a dedicated `chunking/` package, stop and get direction before
    creating a conflicting structure.
- Dependencies:
  - `TL-004`

### Task ID: `TL-006`

- Status: `PENDING_USER_APPROVAL`
- Title: PDF, DOCX, and XLSX parsing plus advanced chunking
- Roadmap Phase(s): Phases 3-4
- Goal: Implement the remaining MVP parsers and chunkers, including page,
  heading, sheet, and cell-range source references.
- Context: These formats are more failure-prone and should build on the parser
  and chunker interfaces already proven by TXT/MD.
- Docs to Read:
  - `docs/roadmap/phase-03-parsers-normalization.md`
  - `docs/roadmap/phase-04-chunking-processed-json.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/repository-structure/ingestion-parsing-models.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
- Files to Inspect:
  - `data/*.docx`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/repository-structure/ingestion-parsing-models.md`
- Likely Files to Modify:
  - `personal_kb/parsers/pdf_parser.py`
  - `personal_kb/parsers/docx_parser.py`
  - `personal_kb/parsers/xlsx_parser.py`
  - `personal_kb/chunking/pdf_chunker.py`
  - `personal_kb/chunking/docx_chunker.py`
  - `personal_kb/chunking/xlsx_chunker.py`
  - `personal_kb/parsers/registry.py`
  - `personal_kb/chunking/registry.py`
  - `tests/unit/parsers/test_pdf_parser.py`
  - `tests/unit/parsers/test_docx_parser.py`
  - `tests/unit/parsers/test_xlsx_parser.py`
  - `tests/unit/chunking/test_pdf_chunker.py`
  - `tests/unit/chunking/test_docx_chunker.py`
  - `tests/unit/chunking/test_xlsx_chunker.py`
- Non-Goals:
  - No OCR
  - No LLM extraction
  - No graph sync
- Implementation Steps:
  1. Implement PDF parsing with `pdfplumber` primary and `PyMuPDF` fallback.
  2. Implement DOCX parsing with `mammoth` primary and `python-docx` fallback.
  3. Implement XLSX parsing with `openpyxl`.
  4. Implement page-aware, heading-aware, and sheet/range-aware chunkers.
  5. Ensure parser failures are surfaced as typed errors for manifest storage.
- Acceptance Criteria:
  - PDF page references are preserved.
  - DOCX section or heading context is preserved where possible.
  - XLSX sheet and cell-range references are preserved.
  - Parser failures remain visible for later manifest failure handling.
- Tests:
  - Unit tests for parser success and fallback paths
  - Unit tests for chunk-source refs
  - Fixture-based tests for representative sample files
- QA Focus:
  - Fallback correctness
  - Source-reference fidelity
  - Failure reporting on malformed inputs
- Risks:
  - Parser-library edge cases will be common.
  - OCR is out of scope and must not be silently approximated.
- Stop Conditions:
  - If scanned PDFs need OCR to satisfy expected behavior, stop; OCR is
    explicitly out of MVP scope.
- Dependencies:
  - `TL-005`

### Task ID: `TL-007`

- Status: `PENDING_USER_APPROVAL`
- Title: Local model client boundaries
- Roadmap Phase(s): Phase 5
- Goal: Implement mockable, lazy-loading LLM, embedding, reranker, and
  structured-extraction client boundaries with schema validation hooks.
- Context: Extraction, retrieval, and Q&A all depend on explicit model
  boundaries that do not leak into services.
- Docs to Read:
  - `docs/roadmap/phase-05-local-model-clients.md`
  - `docs/architecture/model-strategy.md`
  - `docs/implementation/class-design/model-extraction-services.md`
  - `docs/implementation/repository-structure/ingestion-parsing-models.md`
- Files to Inspect:
  - `pyproject.toml`
  - `docs/architecture/model-strategy.md`
  - `docs/roadmap/phase-05-local-model-clients.md`
- Likely Files to Modify:
  - `personal_kb/models/llm_client.py`
  - `personal_kb/models/embedding_client.py`
  - `personal_kb/models/reranker_client.py`
  - `personal_kb/models/extraction_client.py`
  - `tests/unit/models/test_llm_client.py`
  - `tests/unit/models/test_embedding_client.py`
  - `tests/unit/models/test_reranker_client.py`
  - `tests/unit/models/test_extraction_client.py`
- Non-Goals:
  - No extraction orchestration
  - No retrieval scoring
  - No Q&A prompt assembly
  - No import-time model loading
- Implementation Steps:
  1. Implement LM Studio LLM client with structured JSON validation support.
  2. Implement local embedding client returning normalized 1024-d vectors.
  3. Implement reranker client for query-text pair scoring.
  4. Ensure all clients are lazy-loading and mock-friendly.
  5. Add clear failure modes for unavailable local runtimes.
- Acceptance Criteria:
  - Clients are instantiable without loading models at import time.
  - Embeddings are normalized when configured.
  - Reranker scores are returned for query-text pairs.
  - Invalid structured JSON is retried and then fails clearly.
- Tests:
  - Unit tests with mocked LM Studio responses
  - Unit tests for embedding dimension and batch ordering
  - Unit tests for reranker ordering
  - Import safety smoke tests
- QA Focus:
  - Lazy-loading behavior
  - Correct 1024-d embedding contract
  - Retry handling for invalid structured output
- Risks:
  - Model/runtime assumptions may not match the local environment.
  - Wrong dimensions will break Neo4j vector indexing later.
- Stop Conditions:
  - If current local model choices or endpoints must change from the documented
    defaults, stop and confirm before hard-coding alternatives.
- Dependencies:
  - `TL-006`

### Task ID: `TL-008`

- Status: `PENDING_USER_APPROVAL`
- Title: Extraction, embeddings, and document-level aggregation
- Roadmap Phase(s): Phase 6
- Goal: Generate chunk summaries, tags, entities, embeddings, and aggregated
  document metadata, then persist those results in processed records.
- Context: This is the first task that converts parsed chunks into retrieval and
  graph-ready semantic records.
- Docs to Read:
  - `docs/roadmap/phase-06-extraction-embeddings.md`
  - `docs/architecture/model-strategy.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/model-extraction-services.md`
- Files to Inspect:
  - `personal_kb/models/`
  - `personal_kb/schemas/processing.py`
  - `docs/roadmap/phase-06-extraction-embeddings.md`
- Likely Files to Modify:
  - `personal_kb/extraction/structured_extractor.py`
  - `personal_kb/extraction/aggregation.py`
  - `personal_kb/extraction/prompts.py`
  - `tests/unit/extraction/test_structured_extractor.py`
  - `tests/unit/extraction/test_aggregation.py`
  - `tests/integration/extraction/test_chunk_extraction.py`
- Non-Goals:
  - No Neo4j sync
  - No retrieval scoring
  - No answer generation
  - No required LLM-inferred document relationships
- Implementation Steps:
  1. Implement chunk-level summary/tag/entity extraction with schema validation.
  2. Implement chunk embedding generation and persistence fields.
  3. Implement document-level aggregation over chunk metadata.
  4. Normalize tag/entity names with the documented lowercase/trim/collapse
     policy.
  5. Surface retry and failure behavior for invalid LLM output.
- Acceptance Criteria:
  - Each chunk can receive summary, tags, entities, and embedding.
  - Document-level summary/tags/entities are derived from chunk data.
  - Embeddings are available for later JSON and Neo4j storage.
  - Invalid structured output is handled with retries and explicit failures.
- Tests:
  - Unit tests for extraction schema validation
  - Unit tests for aggregation and duplicate merge behavior
  - Integration tests over small TXT/MD fixtures with mocked models
- QA Focus:
  - Grounded extraction shape
  - Name normalization
  - Preservation of chunk/source linkage into aggregated metadata
- Risks:
  - Invalid model JSON is a high-risk failure mode.
  - Slow local runtime can make ingestion unusable if batching/caching is poor.
- Stop Conditions:
  - If extraction requires policy not present in docs for new relationship
    types or canonicalization, stop and ask.
- Dependencies:
  - `TL-007`

### Task ID: `TL-009`

- Status: `PENDING_USER_APPROVAL`
- Title: End-to-end ingestion service and processed-document building
- Roadmap Phase(s): Phases 4 and 6 integration
- Goal: Wire discovery, planning, parsing, chunking, extraction, embedding,
  storage, and manifest updates into a deterministic ingestion pipeline that
  writes `kb_storage` without requiring Neo4j.
- Context: By this point, the building blocks exist but are not yet composed
  into a single typed ingestion flow.
- Docs to Read:
  - `docs/roadmap/phase-04-chunking-processed-json.md`
  - `docs/roadmap/phase-06-extraction-embeddings.md`
  - `docs/architecture/storage-design.md`
  - `docs/implementation/class-design/core-storage-ingestion.md`
- Files to Inspect:
  - `personal_kb/ingestion/`
  - `personal_kb/storage/`
  - `personal_kb/parsers/`
  - `personal_kb/chunking/`
  - `personal_kb/extraction/`
- Likely Files to Modify:
  - `personal_kb/ingestion/document_processor.py`
  - `personal_kb/ingestion/ingestion_service.py`
  - `personal_kb/ingestion/processed_document_builder.py`
  - `tests/integration/ingestion/test_txt_md_ingestion.py`
  - `tests/integration/ingestion/test_multi_format_ingestion.py`
- Non-Goals:
  - No Neo4j setup
  - No graph sync
  - No retrieval or Q&A
- Implementation Steps:
  1. Compose the ingestion pipeline around the existing discovery, planning,
     parser, chunker, extraction, and storage components.
  2. Build processed-document records with stable chunk IDs and source refs.
  3. Persist processed JSON and manifest updates for success, skip, duplicate,
     version, and failure cases.
  4. Keep the entire flow Neo4j-independent at this stage.
  5. Ensure repeated ingestion skips unchanged files.
- Acceptance Criteria:
  - Documents can be ingested to `kb_storage` without Neo4j.
  - Manifest and processed JSON stay consistent across repeated runs.
  - Chunk IDs are stable within a processed document.
  - Unchanged files skip expensive work.
- Tests:
  - Integration tests for TXT/MD end-to-end ingestion
  - Integration tests for failure persistence
  - Integration tests for unchanged-file skip behavior
- QA Focus:
  - Determinism across repeated runs
  - Correct manifest state transitions
  - End-to-end processed JSON completeness
- Risks:
  - Orchestration bugs can break manifest consistency.
  - Premature coupling to Neo4j would violate the source-of-truth boundary.
- Stop Conditions:
  - If the docs still conflict on whether chunking lives under `ingestion/` or
    `chunking/`, do not duplicate both structures; stop and get direction.
- Dependencies:
  - `TL-008`

### Task ID: `TL-010`

- Status: `PENDING_USER_APPROVAL`
- Title: Neo4j driver provider and schema manager
- Roadmap Phase(s): Phase 7
- Goal: Implement Neo4j connectivity, database fallback, `kb setup-db`, and
  schema verification without APOC.
- Context: Retrieval and graph sync require a stable schema layer, but setup
  must remain a CLI/system responsibility rather than an agent capability.
- Docs to Read:
  - `docs/roadmap/phase-07-neo4j-setup-graph-sync.md`
  - `docs/architecture/graph-schema.md`
  - `docs/architecture/neo4j-indexes.md`
  - `docs/architecture/neo4j-setup-sync.md`
  - `docs/implementation/class-design/graph-services.md`
- Files to Inspect:
  - `docs/architecture/neo4j-indexes.md`
  - `docs/architecture/neo4j-setup-sync.md`
  - `personal_kb/schemas/config.py`
- Likely Files to Modify:
  - `personal_kb/graph/neo4j_driver.py`
  - `personal_kb/graph/schema_manager.py`
  - `tests/integration/graph/test_schema_manager.py`
  - `tests/fixtures/graph/`
- Non-Goals:
  - No graph sync from documents yet
  - No retrieval queries
  - No agent exposure
- Implementation Steps:
  1. Implement Neo4j driver creation and configured-database fallback logic.
  2. Implement schema setup for constraints, standard indexes, full-text
     indexes, and the 1024-d vector index.
  3. Implement schema verification and clear missing-schema reporting.
  4. Keep APOC out of the implementation.
- Acceptance Criteria:
  - `kb setup-db` can create schema idempotently.
  - `knowledge_base3` is preferred with fallback to `neo4j`.
  - The vector index uses dimension `1024` and cosine similarity.
  - Missing schema can be detected before ingest/search usage.
- Tests:
  - Integration tests for setup and repeat setup
  - Integration tests for fallback database behavior where feasible
  - Verification of created constraints and indexes
- QA Focus:
  - Neo4j compatibility
  - Schema idempotency
  - Clear failure messages
- Risks:
  - Database mismatch or missing index verification will create subtle runtime
    failures later.
- Stop Conditions:
  - If the target Neo4j version or deployment constraints differ from the docs
    in a way that changes schema syntax or vector-index support, stop and ask.
- Dependencies:
  - `TL-009`

### Task ID: `TL-011`

- Status: `PENDING_USER_APPROVAL`
- Title: Graph sync service and graph query service
- Roadmap Phase(s): Phase 7
- Goal: Sync processed JSON into Neo4j idempotently and expose graph-query
  methods used by retrieval and tool-facing services.
- Context: This task operationalizes the JSON-to-graph boundary while keeping
  `kb_storage` as the rebuildable source of truth.
- Docs to Read:
  - `docs/roadmap/phase-07-neo4j-setup-graph-sync.md`
  - `docs/architecture/neo4j-upsert-patterns.md`
  - `docs/architecture/neo4j-setup-sync.md`
  - `docs/architecture/neo4j-retrieval-queries.md`
  - `docs/implementation/class-design/graph-services.md`
- Files to Inspect:
  - `personal_kb/storage/processed_document_store.py`
  - `docs/architecture/neo4j-upsert-patterns.md`
  - `docs/architecture/graph-schema.md`
- Likely Files to Modify:
  - `personal_kb/graph/graph_sync_service.py`
  - `personal_kb/graph/graph_service.py`
  - `personal_kb/graph/cypher_templates.py`
  - `tests/integration/graph/test_graph_sync.py`
  - `tests/integration/graph/test_graph_service_queries.py`
- Non-Goals:
  - No parsing or chunking
  - No LLM calls
  - No embedding generation
  - No retrieval orchestration
- Implementation Steps:
  1. Translate processed JSON into graph upserts using deterministic `MERGE`
     templates.
  2. Sync documents, chunks, entities, tags, document types, and duplicate or
     version relationships.
  3. Persist `neo4j_synced` state back to the manifest on success or failure.
  4. Implement graph-query methods for document, chunk, entity, tag, keyword,
     vector, and related-document access.
  5. Ensure graph sync is rebuildable and idempotent.
- Acceptance Criteria:
  - Re-syncing the same processed document does not create duplicate graph
    state.
  - Chunk embeddings are written to Neo4j using the documented dimension.
  - Neo4j can be rebuilt from `kb_storage` without re-running parsing or model
    work.
  - Retrieval-facing graph query methods are available behind `GraphService`.
- Tests:
  - Integration tests for JSON-to-Neo4j sync
  - Integration tests for repeated sync idempotency
  - Integration tests for entity/tag/keyword/vector queries
- QA Focus:
  - Graph rebuildability
  - Relationship correctness
  - Manifest sync-state accuracy after failures
- Risks:
  - Graph schema drift is a high-risk failure mode.
  - Sync code can accidentally reintroduce parsing or model dependencies.
- Stop Conditions:
  - If new graph labels or relationships are required beyond the documented MVP
    set, stop and escalate rather than extending the schema ad hoc.
- Dependencies:
  - `TL-010`

### Task ID: `TL-012`

- Status: `PENDING_USER_APPROVAL`
- Title: Retrieval core, search planning, and scoring
- Roadmap Phase(s): Phase 8
- Goal: Implement deterministic search planning, retrieval-layer orchestration,
  hybrid scoring, reranking, and explainable search responses.
- Context: Search must work independently of Q&A and return structured evidence
  rather than answers.
- Docs to Read:
  - `docs/roadmap/phase-08-retrieval-core.md`
  - `docs/architecture/retrieval-design.md`
  - `docs/implementation/tool-contracts/search-plan.md`
  - `docs/implementation/class-design/retrieval-services.md`
  - `docs/implementation/tool-contracts/retrieval-tools.md`
- Files to Inspect:
  - `personal_kb/graph/graph_service.py`
  - `personal_kb/models/embedding_client.py`
  - `personal_kb/models/reranker_client.py`
  - `personal_kb/schemas/search.py`
- Likely Files to Modify:
  - `personal_kb/retrieval/search_plan_builder.py`
  - `personal_kb/retrieval/retrieval_service.py`
  - `personal_kb/retrieval/keyword_search.py`
  - `personal_kb/retrieval/entity_search.py`
  - `personal_kb/retrieval/tag_search.py`
  - `personal_kb/retrieval/vector_search.py`
  - `personal_kb/retrieval/graph_expansion.py`
  - `personal_kb/retrieval/scoring.py`
  - `tests/unit/retrieval/test_search_plan_builder.py`
  - `tests/unit/retrieval/test_scoring.py`
  - `tests/integration/retrieval/test_search_documents.py`
- Non-Goals:
  - No answer generation
  - No tool wrappers
  - No LangGraph routing
- Implementation Steps:
  1. Implement `SearchPlanBuilder` defaults and query-type-specific plans.
  2. Implement keyword, entity, tag, vector, and graph-expansion search paths.
  3. Merge candidates and apply configurable score breakdowns.
  4. Apply reranking after candidate pruning with fallbacks when unavailable.
  5. Return structured result cards with matched chunks, related documents, and
     warnings.
- Acceptance Criteria:
  - `search_documents` returns ranked documents with score breakdowns.
  - Retrieval works without answer generation.
  - Fallback behavior exists when embedding or reranker is unavailable.
  - Query results include source refs and matched chunk summaries.
- Tests:
  - Unit tests for search-plan validation
  - Unit tests for score formulas with and without reranker
  - Integration tests for keyword/entity/tag/vector retrieval
- QA Focus:
  - Score explainability
  - Search-plan behavior
  - Fallback correctness under degraded local-model availability
- Risks:
  - Poor retrieval quality is a release blocker.
  - Hard-coded scoring or plan logic will make tuning difficult.
- Stop Conditions:
  - If the team wants to change the documented default search pipeline or score
    formula, stop and confirm before implementation.
- Dependencies:
  - `TL-011`

### Task ID: `TL-013`

- Status: `PENDING_USER_APPROVAL`
- Title: Source-grounded Q&A service
- Roadmap Phase(s): Phase 9
- Goal: Implement context selection, grounded answer generation, citations,
  warnings, and missing-information handling for `answer_question`.
- Context: Q&A must sit on top of retrieval evidence and must not answer from
  model prior knowledge when sources are missing.
- Docs to Read:
  - `docs/roadmap/phase-09-qa-service.md`
  - `docs/architecture/qa-design.md`
  - `docs/implementation/class-design/qa-services.md`
  - `docs/implementation/tool-contracts/qa-tools.md`
- Files to Inspect:
  - `personal_kb/retrieval/retrieval_service.py`
  - `personal_kb/models/llm_client.py`
  - `personal_kb/schemas/qa.py`
- Likely Files to Modify:
  - `personal_kb/qa/context_builder.py`
  - `personal_kb/qa/answer_generator.py`
  - `personal_kb/qa/citation_builder.py`
  - `personal_kb/qa/qa_service.py`
  - `tests/unit/qa/test_context_builder.py`
  - `tests/unit/qa/test_answer_generator.py`
  - `tests/integration/qa/test_answer_question.py`
- Non-Goals:
  - No FAQ memory
  - No tool wrappers
  - No agent orchestration
- Implementation Steps:
  1. Build answer context from retrieval results with top-k chunk limits.
  2. Implement source-grounded answer prompting via the local LLM client.
  3. Build citations and source-document records from supporting chunks.
  4. Surface missing information and low-confidence warnings explicitly.
  5. Ensure document-text Q&A can include `supporting_chunks.text`.
- Acceptance Criteria:
  - `answer_question` returns answer, confidence, source documents, supporting
    chunks, warnings, and missing information.
  - Answers do not rely on unsupported prior knowledge when context is missing.
  - Source refs include page, section, sheet, or cell range when available.
- Tests:
  - Unit tests for context selection and include-text behavior
  - Unit tests for grounded/no-context answer cases
  - Integration tests for answer serialization and citation correctness
- QA Focus:
  - Faithfulness to supporting chunks
  - Warning and missing-information behavior
  - Citation traceability
- Risks:
  - Hallucination risk remains high if grounding validation is weak.
  - Overlong context will hurt latency and answer quality.
- Stop Conditions:
  - If Q&A behavior requires a new memory or caching policy not defined in MVP,
    stop and ask before adding stateful features.
- Dependencies:
  - `TL-012`

### Task ID: `TL-014`

- Status: `PENDING_USER_APPROVAL`
- Title: Document inspection services and `KnowledgeToolService` facade
- Roadmap Phase(s): Phase 10
- Goal: Implement the read-only document, duplicate, relationship, and facade
  layer that coordinates retrieval, Q&A, graph, and storage services for tool
  callers.
- Context: Tools must stay thin; the facade and supporting read services are
  where adapter-independent coordination belongs.
- Docs to Read:
  - `docs/roadmap/phase-10-knowledge-tool-service-structured-tools.md`
  - `docs/implementation/tool-contracts/knowledge-tool-service.md`
  - `docs/implementation/class-design/tool-services.md`
  - `docs/implementation/tool-contracts/retrieval-tools.md`
  - `docs/implementation/tool-contracts/qa-tools.md`
- Files to Inspect:
  - `personal_kb/retrieval/retrieval_service.py`
  - `personal_kb/qa/qa_service.py`
  - `personal_kb/graph/graph_service.py`
  - `personal_kb/storage/processed_document_store.py`
- Likely Files to Modify:
  - `personal_kb/tools/knowledge_tool_service.py`
  - `personal_kb/documents/document_service.py` or another user-approved home
    for document read services
  - `personal_kb/documents/duplicate_service.py` or equivalent
  - `personal_kb/documents/relationship_service.py` or equivalent
  - `tests/unit/tools/test_knowledge_tool_service.py`
  - `tests/unit/documents/`
- Non-Goals:
  - No LangChain wrappers yet
  - No LangGraph agent
  - No business logic in adapters
- Implementation Steps:
  1. Implement document summary and chunk inspection services over processed
     JSON and graph data.
  2. Implement duplicate and relationship explanation services.
  3. Implement `KnowledgeToolService` as the single facade used by tools and
     CLI read/query commands.
  4. Keep Cypher, parsing, scoring, and model inference out of the facade.
- Acceptance Criteria:
  - Facade methods delegate cleanly to lower services.
  - Related-document, summary, chunk, duplicate, and relationship queries are
    available through typed request/response schemas.
  - The facade does not contain direct Cypher, parsing, or scoring logic.
- Tests:
  - Unit tests for facade delegation
  - Unit tests for document-summary and chunk inspection behavior
  - Unit tests for duplicate and relationship explanation flows
- QA Focus:
  - Separation of concerns
  - Contract completeness across all read/query methods
  - Absence of business logic inside the facade
- Risks:
  - Service-placement ambiguity in docs can lead to the wrong package layout.
  - Facade bloat will make tool wrappers and CLI drift-prone.
- Stop Conditions:
  - If the team must decide where `DocumentService`, `DuplicateService`, and
    `RelationshipService` live, stop and resolve that before creating a new
    package structure.
- Dependencies:
  - `TL-013`

### Task ID: `TL-015`

- Status: `PENDING_USER_APPROVAL`
- Title: LangChain StructuredTool wrappers and tool registry
- Roadmap Phase(s): Phase 10
- Goal: Expose the approved read-only MVP tool surface as schema-validated
  wrappers over `KnowledgeToolService`.
- Context: Tool wrappers are adapters only and must not duplicate business
  logic from the facade or lower services.
- Docs to Read:
  - `docs/roadmap/phase-10-knowledge-tool-service-structured-tools.md`
  - `docs/implementation/tool-contracts/langchain-structured-tools.md`
  - `docs/implementation/class-design/tool-services.md`
  - `docs/architecture/agent-design.md`
- Files to Inspect:
  - `personal_kb/tools/knowledge_tool_service.py`
  - `docs/implementation/tool-contracts/langchain-structured-tools.md`
  - `docs/implementation/tool-contracts/knowledge-tool-service.md`
- Likely Files to Modify:
  - `personal_kb/tools/structured_tools.py` or `personal_kb/tools/langchain_tools.py`
    after resolving the naming conflict
  - `personal_kb/tools/tool_registry.py`
  - `tests/unit/tools/test_structured_tools.py`
  - `tests/unit/tools/test_tool_registry.py`
- Non-Goals:
  - No agent workflow
  - No mutation tools
  - No direct Neo4j or model calls in wrappers
- Implementation Steps:
  1. Implement wrappers for the approved MVP tool list.
  2. Validate inputs with Pydantic schemas and serialize responses to
     JSON-compatible dicts.
  3. Add a registry or factory that provides the allowed tool set.
  4. Ensure only read/query tools are exposed.
- Acceptance Criteria:
  - Every approved tool has an args schema and JSON-serializable response.
  - Every wrapper calls `KnowledgeToolService` only.
  - No wrapper performs Cypher, reranking, parsing, or answer-generation logic.
- Tests:
  - Unit tests for args-schema wiring
  - Unit tests for delegation to `KnowledgeToolService`
  - Contract tests for JSON serialization
- QA Focus:
  - Adapter thinness
  - Allowed tool list only
  - Serialization fidelity
- Risks:
  - Naming conflict between `structured_tools.py` and `langchain_tools.py`
    could create duplicate patterns.
- Stop Conditions:
  - If the project must choose a canonical wrapper filename or adapter location,
    stop and confirm before creating parallel implementations.
- Dependencies:
  - `TL-014`

### Task ID: `TL-016`

- Status: `PENDING_USER_APPROVAL`
- Title: LangGraph agent orchestration
- Roadmap Phase(s): Phase 11
- Goal: Implement the internal LangGraph agent workflow using only approved
  StructuredTools and read/query routes.
- Context: The agent is an orchestration layer, not a business-logic layer, and
  must not control ingestion or other write actions.
- Docs to Read:
  - `docs/roadmap/phase-11-langgraph-agent.md`
  - `docs/architecture/agent-design.md`
  - `docs/implementation/class-design/agent-services.md`
  - `docs/implementation/tool-contracts/langchain-structured-tools.md`
- Files to Inspect:
  - `personal_kb/tools/tool_registry.py`
  - `docs/architecture/agent-design.md`
  - `docs/implementation/class-design/agent-services.md`
- Likely Files to Modify:
  - `personal_kb/agent/state.py` or `personal_kb/agents/state.py`
  - `personal_kb/agent/query_router.py` or `personal_kb/agents/router.py`
  - `personal_kb/agent/graph.py` or `personal_kb/agents/langgraph_agent.py`
  - `personal_kb/agent/nodes.py`
  - `tests/unit/agent/test_query_router.py`
  - `tests/unit/agent/test_langgraph_agent.py`
- Non-Goals:
  - No direct repository/service access from nodes
  - No ingestion, rebuild, sync, delete, move, or rename capabilities
- Implementation Steps:
  1. Define agent state and route types.
  2. Implement deterministic routing for the documented query classes.
  3. Build the LangGraph workflow around routing, search-plan creation, tool
     execution, and response assembly.
  4. Preserve warnings from tool responses into final agent output.
- Acceptance Criteria:
  - The agent uses LangChain StructuredTools only.
  - The agent cannot reach ingestion, rebuild, sync, or destructive actions.
  - Route examples map to the expected tool paths.
  - Responses are structured for CLI or future API use.
- Tests:
  - Unit tests for deterministic route selection
  - Unit tests for agent invocation with mocked tools
  - Integration tests for search and ask flows once the tool layer is stable
- QA Focus:
  - Safety boundaries
  - Route-to-tool correctness
  - Warning preservation
- Risks:
  - Docs disagree on `agent/` versus `agents/` package naming.
  - Business logic can leak into nodes if the orchestration boundary slips.
- Stop Conditions:
  - If package naming for the agent layer is still unresolved, stop and ask
    before creating duplicate agent package trees.
- Dependencies:
  - `TL-015`

### Task ID: `TL-017`

- Status: `PENDING_USER_APPROVAL`
- Title: CLI integration and command formatting
- Roadmap Phase(s): Phase 12
- Goal: Implement the user-facing `kb` CLI over setup, ingestion, search, ask,
  related, duplicates, status, and JSON formatting paths.
- Context: The CLI is the primary developer-facing interface and must reuse the
  same services and tool facade as the agent for read/query behavior.
- Docs to Read:
  - `docs/roadmap/phase-12-cli-integration.md`
  - `docs/architecture/agent-design.md`
  - `docs/implementation/class-design/tool-services.md`
  - `docs/implementation/repository-structure/cli-evaluation-scripts-tests.md`
- Files to Inspect:
  - `personal_kb/cli/main.py`
  - `personal_kb/tools/knowledge_tool_service.py`
  - `personal_kb/ingestion/ingestion_service.py`
  - `personal_kb/graph/schema_manager.py`
- Likely Files to Modify:
  - `personal_kb/cli/main.py`
  - `personal_kb/cli/commands.py`
  - `personal_kb/cli/formatters.py`
  - `tests/unit/cli/test_commands.py`
  - `tests/integration/cli/test_cli_flows.py`
- Non-Goals:
  - No web UI
  - No Telegram bot
  - No external writes
- Implementation Steps:
  1. Implement CLI command parsing for setup, ingest, search, ask, related,
     duplicates, status, and JSON output.
  2. Keep command handlers thin and route read/query calls through
     `KnowledgeToolService`.
  3. Route ingest and setup directly to the corresponding core services.
  4. Provide human-readable formatting by default and `--json` output when
     requested.
- Acceptance Criteria:
  - CLI commands work from a fresh checkout after environment setup.
  - Missing Neo4j schema produces helpful errors.
  - `kb ingest data` can sync Neo4j after successful processing.
  - `kb search` and `kb ask` reuse the same read/query contracts as the agent.
- Tests:
  - Unit tests for command parsing and handler delegation
  - Integration tests for CLI happy paths
  - Integration tests for `--json` output
- QA Focus:
  - Handler thinness
  - Output correctness and usability
  - Error message clarity
- Risks:
  - CLI drift from tool/agent behavior will make debugging confusing.
  - Thin-handler discipline is easy to break late in implementation.
- Stop Conditions:
  - If a new command outside the documented MVP command set is requested,
    stop and confirm scope before adding it.
- Dependencies:
  - `TL-016`

### Task ID: `TL-018`

- Status: `PENDING_USER_APPROVAL`
- Title: Benchmark loader, metrics, and evaluation runner
- Roadmap Phase(s): Phase 13
- Goal: Add a small benchmark suite with inspectable retrieval and Q&A metrics
  so release readiness can be measured rather than guessed.
- Context: Retrieval quality is a stated release risk and requires dedicated
  benchmark instrumentation.
- Docs to Read:
  - `docs/roadmap/phase-13-benchmark-evaluation.md`
  - `docs/product-requirements/validation-and-acceptance.md`
  - `docs/architecture/retrieval-design.md`
  - `docs/architecture/qa-design.md`
  - `docs/implementation/repository-structure/cli-evaluation-scripts-tests.md`
- Files to Inspect:
  - `benchmark/`
  - `personal_kb/retrieval/`
  - `personal_kb/qa/`
  - `personal_kb/cli/`
- Likely Files to Modify:
  - `benchmark/benchmark.jsonl`
  - `personal_kb/evaluation/benchmark_loader.py`
  - `personal_kb/evaluation/retrieval_metrics.py`
  - `personal_kb/evaluation/qa_metrics.py`
  - `personal_kb/evaluation/evaluator.py`
  - `tests/unit/evaluation/`
  - `tests/integration/evaluation/test_benchmark_runner.py`
- Non-Goals:
  - No large-scale evaluation framework
  - No post-MVP tuning platform
- Implementation Steps:
  1. Define the benchmark record schema and add initial cases.
  2. Implement retrieval metrics and Q&A evaluation helpers.
  3. Implement a runner that outputs inspectable failures.
  4. Expose benchmark execution through the CLI or a documented entrypoint.
- Acceptance Criteria:
  - The benchmark can be executed locally.
  - Failures are inspectable by query, returned docs, scores, chunks, and
    source refs.
  - Retrieval and Q&A metrics align with the roadmap definitions.
- Tests:
  - Unit tests for metric calculations
  - Unit tests for benchmark loading and schema validation
  - Integration tests for end-to-end benchmark execution
- QA Focus:
  - Metric correctness
  - Failure inspectability
  - Benchmark data quality
- Risks:
  - Weak benchmark cases will hide retrieval quality problems.
  - Uninspectable failures will block tuning.
- Stop Conditions:
  - If the team wants to change the acceptance benchmark size or metrics beyond
    the documented set, stop and confirm first.
- Dependencies:
  - `TL-017`

### Task ID: `TL-019`

- Status: `PENDING_USER_APPROVAL`
- Title: MVP hardening, regression coverage, and operator docs
- Roadmap Phase(s): Phase 14
- Goal: Harden failure handling, logging, config validation, regression tests,
  and user/developer documentation so the MVP can be run repeatedly.
- Context: Stability, graceful degradation, and repeatability are explicit MVP
  release gates after the core functionality exists.
- Docs to Read:
  - `docs/roadmap/phase-14-mvp-hardening.md`
  - `docs/product-requirements/risks-and-future-requirements.md`
  - `docs/product-requirements/validation-and-acceptance.md`
  - `docs/architecture/overview.md`
  - `docs/implementation/repository-structure/project-root-and-runtime-data.md`
- Files to Inspect:
  - `README.md`
  - `personal_kb/core/`
  - `personal_kb/cli/`
  - `tests/`
  - `benchmark/`
- Likely Files to Modify:
  - `README.md`
  - `personal_kb/core/logging.py`
  - `personal_kb/core/config_loader.py`
  - `personal_kb/cli/formatters.py`
  - `tests/integration/`
  - `tests/unit/`
  - troubleshooting docs under `docs/` if needed
- Non-Goals:
  - No MCP adapter
  - No external source connectors
  - No FAQ memory
  - No OCR
  - No web UI
- Implementation Steps:
  1. Improve error handling for failed docs, missing schema, Neo4j downtime,
     and unavailable reranker/model paths.
  2. Add structured logging with safe defaults that avoid dumping full document
     text.
  3. Tighten config validation and startup diagnostics.
  4. Add regression coverage for ingestion and retrieval loops.
  5. Update README and troubleshooting guidance to match the implemented MVP.
- Acceptance Criteria:
  - Failed documents do not break full ingestion.
  - Neo4j downtime does not destroy processed JSON state.
  - Search degrades gracefully when reranker is unavailable.
  - Logs avoid full document text by default.
  - Repeated runs do not corrupt manifest or graph state.
- Tests:
  - Integration tests for failed-document resilience
  - Integration tests for Neo4j outage behavior
  - Integration tests for reranker-unavailable fallback
  - Regression tests covering repeated ingest/sync cycles
- QA Focus:
  - Operational resilience
  - Log safety
  - Repeatability across multiple runs
- Risks:
  - Hardening work is easy to defer but directly affects MVP usability.
  - Logging mistakes may leak document contents unexpectedly.
- Stop Conditions:
  - If this task reveals product-scope expansion beyond hardening, stop and
    split the work rather than smuggling new features into the release pass.
- Dependencies:
  - `TL-018`

## Cross-Task QA Plan

- After each approved implementation task, run focused QA before continuing.
- Favor unit tests for schema, utility, and wrapper behavior.
- Favor integration tests for ingestion, Neo4j, retrieval, Q&A, and CLI flows.
- Keep regression coverage for repeated ingest and sync cycles.
- Use the benchmark suite as the main release-quality signal after the core
  search and Q&A stack exists.

## Global Risks

- Documentation conflicts may cause wasted implementation if not resolved early.
- Retrieval quality is a release blocker even if the system is feature-complete.
- Invalid structured model output is a high-risk failure mode in extraction and
  Q&A.
- Graph rebuildability depends on preserving `kb_storage/` as the true source
  of processed state.
- Tool and agent layers can easily accumulate business logic if boundaries are
  not enforced during reviews.

## Open Questions

1. `docs/adr/` was requested as input but does not exist in the current repo.
   Is that directory intentionally absent, or should ADRs be added before
   implementation begins?
2. Which config file path is authoritative: `configs/config.yaml` or
   `configs/default.yaml`?
3. Which environment template is authoritative for bootstrap:
   `env_sample` or `.env.example`?
4. Which package path is authoritative for the agent layer:
   `personal_kb/agent/` or `personal_kb/agents/`?
5. Which file is authoritative for LangChain wrappers:
   `personal_kb/tools/structured_tools.py` or
   `personal_kb/tools/langchain_tools.py`?
6. Which package should own read-only document coordination services such as
   `DocumentService`, `DuplicateService`, and `RelationshipService`?
7. Is the long-term package plan to keep a dedicated `personal_kb/chunking/`
   package, or should chunking live under `personal_kb/ingestion/`?

## Approval Request

This plan is approved and currently in progress. `TL-001` has been implemented
and passed QA. The next implementation handoff still requires explicit approval
before handing off only Task `TL-002` to the Python Engineer.
