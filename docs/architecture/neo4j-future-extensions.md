# Neo4j Future Extensions

## Purpose

This file preserves graph schema extension points that are explicitly not implemented in the MVP.

## When to read this

Read this file when planning post-MVP graph schema work, source-specific graph nodes, FAQ/QA memory, user feedback, external source relationships, or optional LLM-inferred relationships.

## Related files

- [graph-schema.md](graph-schema.md)
- [neo4j-node-schemas.md](neo4j-node-schemas.md)
- [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md)
- [qa-design.md](qa-design.md)
- [agent-design.md](agent-design.md)
- [storage-design.md](storage-design.md)

## Source of truth

This file is authoritative for future Neo4j schema extension labels, relationships, and the MVP boundary that keeps these extensions optional and unimplemented.

## Content

### Responsibility

Future graph extensions keep likely architecture paths visible without making them part of MVP graph sync, retrieval, or Q&A behavior.

These labels are not implemented in MVP, but the schema leaves space for them.

### QA/FAQ memory

Future nodes:

```text
(:Question)
(:Answer)
(:FAQEntry)
(:SearchQuery)
(:UserFeedback)
```

Future relationships:

```text
(:Question)-[:ANSWERED_BY]->(:Answer)
(:Answer)-[:SUPPORTED_BY]->(:Chunk)
(:Answer)-[:USES_DOCUMENT]->(:Document)
(:Question)-[:ABOUT]->(:Entity)
(:Question)-[:HAS_TAG]->(:Tag)
(:FAQEntry)-[:SIMILAR_TO]->(:FAQEntry)
```

Future purpose:

```text
frequent question reuse
answer freshness validation
stale answer detection after document version changes
user feedback tracking
```

### External source nodes

Future source-specific nodes:

```text
(:Source)
(:JiraIssue)
(:ConfluencePage)
(:GmailThread)
(:GoogleDoc)
(:GoogleSheet)
(:GoogleSlide)
```

Future relationships:

```text
(:Document)-[:FROM_SOURCE]->(:Source)
(:Document)-[:REPRESENTS]->(:ConfluencePage)
(:Document)-[:LINKED_TO_TASK]->(:JiraIssue)
(:Document)-[:DISCUSSED_IN]->(:GmailThread)
(:Document)-[:REPRESENTS]->(:GoogleDoc)
(:Document)-[:REPRESENTS]->(:GoogleSheet)
(:Document)-[:REPRESENTS]->(:GoogleSlide)
```

### LLM-inferred relationships

Future optional relationships:

```text
(:Document)-[:SUPPORTS]->(:Document)
(:Document)-[:CONTRADICTS]->(:Document)
(:Document)-[:UPDATES]->(:Document)
(:Document)-[:EXPLAINS]->(:Document)
(:Document)-[:REFERENCES_DECISION]->(:Entity)
```

These must remain optional until deterministic relationships are stable and evaluated.

### Conflict / Review needed

Earlier architecture notes in this folder mentioned possible future `(:Section)`, `(:Summary)`, and `(:DocumentVersion)` nodes. The Neo4j graph schema source file for this split says:

- store summaries as node properties, not `Summary` nodes;
- store section/page/sheet/range inside `Chunk.source_ref` properties, not `Section` nodes;
- do not add `Section`, `Summary`, `Question`, `Answer`, `FAQEntry`, `Source`, or external source nodes in MVP.

Treat `Section`, `Summary`, and `DocumentVersion` nodes as review-needed ideas, not accepted future schema until a later architecture decision explicitly reintroduces them.

## Dependencies

- MVP schema boundary in [graph-schema.md](graph-schema.md)
- Source connector planning in [storage-design.md](storage-design.md)
- Grounded answer behavior in [qa-design.md](qa-design.md)
- Agent/tool boundaries in [agent-design.md](agent-design.md)

## Failure modes / risks

| Risk | Impact | Mitigation |
|---|---|---|
| Future labels leak into MVP | Graph sync and retrieval become harder before validation | Keep these labels out of MVP upserts and setup. |
| LLM-inferred relations are trusted too early | Incorrect graph links harm retrieval and Q&A trust | Wait until deterministic relationships are stable and evaluated. |
| FAQ memory stores stale answers | Answers can become unsupported after document changes | Add freshness validation before implementing QA memory. |
| Source-specific nodes duplicate document identity | Confusing source/document model | Keep `Document` as the core graph record and introduce source-specific nodes only with clear relationships. |

## Validation

Before implementing any future extension:

- confirm deterministic MVP relationships have benchmark coverage;
- define source-of-truth ownership for new labels and relationships;
- add constraints/indexes for new labels;
- define graph sync input fields in processed JSON or connector storage;
- add validation queries and acceptance criteria;
- update [graph-schema.md](graph-schema.md), [neo4j-node-schemas.md](neo4j-node-schemas.md), [neo4j-relationship-schemas.md](neo4j-relationship-schemas.md), [neo4j-indexes.md](neo4j-indexes.md), and [neo4j-upsert-patterns.md](neo4j-upsert-patterns.md) as needed.

## Update rules

Update this file when future graph labels, future relationships, FAQ/QA memory design, external source node design, or LLM-inferred relationship policy changes.
