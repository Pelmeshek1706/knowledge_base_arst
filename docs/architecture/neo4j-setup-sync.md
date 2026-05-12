# Neo4j Setup and Graph Sync

## Purpose

This file defines Neo4j setup behavior, database fallback, the no-APOC rule, setup script responsibilities, and graph sync boundaries.

## When to read this

Read this file when changing `kb setup-db`, `--auto-setup-db`, Neo4j database selection, setup verification, graph sync inputs/outputs, graph sync service boundaries, or retry/idempotency behavior.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-indexes.md](neo4j-indexes.md)
- [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- [neo4j-validation-risks.md](neo4j-validation-risks.md)
- [storage-design.md](storage-design.md)
- [retrieval-design.md](retrieval-design.md)

## Source of truth

This file is authoritative for Neo4j database selection, setup command behavior, fallback behavior, no-APOC constraints, setup script order, graph sync input/output, and graph sync boundaries.

## Content

### Responsibility

Setup prepares the Neo4j database schema. Graph sync reads processed JSON and writes graph state to Neo4j.

These operations are deterministic infrastructure behavior. They are not agent tools.

### Public API / Methods

Primary schema initialization command:

```bash
kb setup-db
```

Optional ingest mode:

```bash
kb ingest data --auto-setup-db
```

Recommended explicit database options:

```bash
kb setup-db --database knowledge_base3
kb setup-db --database neo4j
```

### Database selection

Configured database:

```text
knowledge_base3
```

Fallback database:

```text
neo4j
```

Algorithm:

```text
1. Try connecting to knowledge_base3.
2. If unavailable:
   a. if multi-database support is available, create/use knowledge_base3;
   b. otherwise warn and fallback to neo4j.
3. Run constraints.
4. Run standard indexes.
5. Run full-text indexes.
6. Run vector index.
7. Verify index status.
8. Write active database to runtime status/config if needed.
```

Existing architecture note:

```text
kb ingest should fail with a clear message if schema is missing and --auto-setup-db is not provided.
```

### No APOC

Do not require APOC in MVP.

All setup and sync operations should use standard Cypher and the Neo4j Python driver.

### Graph sync rules

Graph sync reads:

```text
kb_storage/documents/<document_id>.json
```

and writes graph state to Neo4j.

Graph sync must be:

```text
idempotent
retry-safe
schema-validated
free of LLM calls
free of parsing/chunking logic
free of source file mutation
```

Existing architecture note:

```text
Graph sync should write sync status back to the manifest, including failed sync state when Neo4j is unavailable or partial sync occurs.
```

### Setup script summary

`kb setup-db` should execute:

```text
1. connect to configured database
2. fallback if needed
3. create constraints
4. create standard indexes
5. create full-text indexes
6. create vector index
7. verify schema
```

## Inputs

- Neo4j URI and credentials from configuration.
- Configured database `knowledge_base3`.
- Fallback database `neo4j`.
- Processed JSON files in `kb_storage/documents/<document_id>.json`.
- Schema/index definitions from [neo4j-indexes.md](neo4j-indexes.md).

## Outputs

- Neo4j constraints, indexes, full-text indexes, and vector index.
- Neo4j nodes and relationships created or updated through graph sync.
- Active database runtime status/config when needed.
- Manifest sync status when graph sync succeeds or fails.

## Side effects

- `kb setup-db` mutates Neo4j schema state by creating missing constraints and indexes.
- Graph sync mutates Neo4j graph state by upserting nodes and relationships.
- Graph sync may update manifest/runtime sync status.
- Setup and sync must not mutate source documents.

## What this must not do

- Do not require APOC.
- Do not parse files.
- Do not call LLMs.
- Do not generate embeddings.
- Do not decide chunking.
- Do not mutate source files.
- Do not expose graph rebuild or ingestion as agent tools.

## Dependencies

- Constraints and indexes from [neo4j-indexes.md](neo4j-indexes.md)
- Node schemas from [neo4j-node-schemas.md](neo4j-node-schemas.md)
- Relationship schemas from [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- Upsert Cypher from [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md)
- Processed JSON and manifest from [storage-design.md](storage-design.md)

## Failure modes / risks

| Failure | Mitigation |
|---|---|
| Neo4j unavailable | Keep JSON, mark `neo4j_synced=false`, and return a clear system error. |
| Configured database unavailable | Fallback from `knowledge_base3` to `neo4j` when needed. |
| Schema missing during ingest | Tell user to run `kb setup-db`, unless `--auto-setup-db` was passed. |
| Partial graph sync | Retry idempotently. |
| Neo4j schema drift | Keep JSON as primary processed storage. |
| Neo4j database mismatch | Use configured `knowledge_base3` with fallback to `neo4j`. |
| APOC dependency creep | Avoid APOC in MVP. |

## Validation

Validate setup and sync by checking that:

- `kb setup-db` can run repeatedly without errors;
- setup uses `knowledge_base3` when available;
- setup warns and falls back to `neo4j` when required;
- setup creates constraints, standard indexes, full-text indexes, and the vector index;
- setup verifies index status after creation;
- no setup or sync operation requires APOC;
- graph sync is idempotent and retry-safe;
- re-running graph sync does not duplicate nodes or relationships;
- graph sync reads only `kb_storage/documents/<document_id>.json`;
- graph sync does not call LLMs, generate embeddings, parse files, decide chunking, or mutate source files;
- sync status is written back to the manifest/runtime status when applicable.

## Update rules

Update this file when setup commands, database fallback behavior, no-APOC policy, setup ordering, graph sync boundaries, graph sync side effects, or manifest sync status behavior changes.
