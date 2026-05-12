# Phase 7: Neo4j Setup + Graph Sync

## Purpose

Create Neo4j schema and sync processed JSON into graph/vector state.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 6: Extraction + Embeddings](phase-06-extraction-embeddings.md)

## Outputs

```text
personal_kb/graph/
  neo4j_driver.py
  schema_manager.py
  graph_sync_service.py
  graph_repository.py
```

## In scope

- Neo4j driver boundary.
- Schema manager.
- Graph sync service.
- Graph repository.
- `kb setup-db`.
- Optional `kb ingest data --auto-setup-db`.
- Constraints, indexes, and vector index.
- Idempotent graph sync from `kb_storage`.
- MVP graph nodes and relationships.

## Out of scope

- APOC dependency.
- LLM reprocessing during graph rebuild.
- Retrieval query behavior beyond graph state required by later phases.

## Related docs

- [Roadmap index](index.md)
- [Graph schema](../architecture/graph-schema.md)
- [Neo4j setup and sync](../architecture/neo4j-setup-sync.md)
- [Neo4j indexes](../architecture/neo4j-indexes.md)
- [Phase 8: Retrieval Core](phase-08-retrieval-core.md)

## Source of truth

This file is authoritative for Phase 7 Neo4j setup, graph sync, MVP graph
nodes, relationships, and graph acceptance criteria.

## Implementation checklist

CLI commands:

```bash
kb setup-db
kb ingest data --auto-setup-db
```

Schema behavior:

- Primary database target: `knowledge_base3`.
- Fallback database: `neo4j`.
- APOC is not required.
- `kb setup-db` is the primary setup mode.
- `--auto-setup-db` is optional.

MVP graph nodes:

```text
(:Document)
(:Chunk)
(:Entity)
(:Tag)
(:DocumentType)
```

MVP relationships:

```text
(:Document)-[:CONTAINS]->(:Chunk)
(:Document)-[:HAS_TAG]->(:Tag)
(:Chunk)-[:HAS_TAG]->(:Tag)
(:Document)-[:HAS_TYPE]->(:DocumentType)
(:Chunk)-[:MENTIONS]->(:Entity)
(:Document)-[:MENTIONS]->(:Entity)
(:Document)-[:DUPLICATE_OF]->(:Document)
(:Document)-[:NEWER_VERSION_OF]->(:Document)
(:Document)-[:RELATED_TO]->(:Document)
```

## Exit criteria

- `kb setup-db` creates constraints, indexes, and vector index.
- Graph sync is idempotent.
- Re-running sync does not create duplicate nodes or edges.
- Neo4j can be rebuilt from `kb_storage` without LLM reprocessing.
- Vector index uses dimension `1024` and cosine similarity.

## Validation

- Run `kb setup-db` and confirm constraints, indexes, and vector index exist.
- Sync the same processed JSON more than once and confirm no duplicate nodes or
  edges are created.
- Rebuild Neo4j from `kb_storage` without LLM reprocessing.
- Confirm vector index dimension is `1024` and similarity is cosine.

## Failure modes / risks

- Graph schema drift is a high-risk failure mode; keep JSON as source of truth
  and sync idempotently.
- Duplicate/version confusion can appear in graph relationships if Phase 2
  decisions are not preserved.
- Requiring APOC would violate the MVP setup constraint.

## Update rules

Update this file when Neo4j database selection, setup behavior, graph nodes,
relationships, vector index settings, or sync idempotency requirements change.
