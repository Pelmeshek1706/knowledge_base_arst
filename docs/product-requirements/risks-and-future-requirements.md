# Risks and Future Requirements

## Purpose

This file preserves product risks, mitigations, and future requirements that are outside or beyond the MVP.

## When to read this

Read this when assessing implementation risk, deferring scope, planning future connectors, or considering future UI, memory, relationship, or write-action capabilities.

## Related files

- [Product requirements index](index.md)
- [Goals and scope](goals-and-scope.md)
- [Non-functional requirements](non-functional-requirements.md)
- [Search, Q&A, CLI, and agent requirements](search-qa-cli-agent-requirements.md)
- [Release plan](release-plan.md)

## Source of truth

This file is authoritative for Product Requirements risks, mitigations, and future requirements.

## Content

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Poor extraction quality | Weak graph and search | Validate extraction on benchmark; add schema retries. |
| Bad chunking | Poor retrieval and Q&A | Use file-type-specific chunkers; inspect examples. |
| Local model output instability | Invalid JSON / hallucinated metadata | Use Pydantic validation, retry prompts, fallback defaults. |
| Slow ingestion | Poor developer experience | Skip unchanged files, hash early, store JSON state, avoid duplicate reprocessing. |
| Neo4j schema drift | Broken graph sync | Use `kb setup-db`, versioned schemas, idempotent upserts. |
| Duplicate/version confusion | Incorrect canonical docs | Use deterministic canonical rule: newest modified_at, fallback ingested_at. |
| Search latency >10s | Poor usability | Candidate pruning, top-k limits, rerank only after narrowing candidates. |
| Too much agent autonomy | Unsafe operations | Agent has search-only tools in MVP. |
| Business logic inside tools | Hard to test and duplicate across CLI/MCP/LangGraph | Keep tools as thin wrappers over `KnowledgeToolService`. |
| Premature MCP integration | Architecture complexity before core tools are stable | Use LangGraph + StructuredTools in MVP; add MCP adapter later. |
| Sensitive data exposure in logs | Privacy risk | Do not log full text by default. |
| Overengineering | Delayed MVP | Build schemas/config/manifest first, then parsers, then graph. |

## Future Requirements

### External Source Connectors

Future connectors:

- ConfluenceConnector
- JiraConnector
- GmailConnector
- GoogleDriveConnector
- GoogleDocsConnector
- GoogleSheetsConnector
- GoogleSlidesConnector

All must output the same internal `RawDocument` contract.

### Source-Specific Graph Nodes

Future nodes:

```text
(:ConfluencePage)
(:JiraIssue)
(:GmailThread)
(:GoogleDoc)
(:GoogleSheet)
(:GoogleSlide)
(:Source)
```

### FAQ/QA Memory

Future behavior:

1. User asks question.
2. System checks FAQ memory first.
3. System verifies whether supporting documents changed.
4. If still valid, returns existing answer.
5. If stale, regenerates answer and updates FAQ entry.

Future nodes:

```text
(:Question)
(:Answer)
(:FAQEntry)
(:SearchQuery)
(:UserFeedback)
```

### LLM-Inferred Relationships

Future relationship types:

```text
(:Document)-[:SUPPORTS]->(:Document)
(:Document)-[:CONTRADICTS]->(:Document)
(:Document)-[:UPDATES]->(:Document)
(:Document)-[:EXPLAINS]->(:Document)
(:Document)-[:REFERENCES_DECISION]->(:Entity)
```

### User Interfaces

Future UI options:

- Telegram bot.
- Local web app.
- React UI.
- Obsidian-like document explorer.
- Neo4j Bloom / graph visualization.
- VS Code extension.

### Controlled Write Actions

Future write actions must be confirmation-based:

- create Confluence page draft;
- link document to Jira issue;
- prepare email with document links;
- suggest file move;
- suggest file rename.

Destructive actions require explicit confirmation.

## Dependencies

- MVP scope and non-goals in [goals-and-scope.md](goals-and-scope.md).
- Agent and MCP boundaries in [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md).
- Non-functional constraints in [non-functional-requirements.md](non-functional-requirements.md).

## Failure modes / risks

- Future connectors can fracture the system if they do not output the same internal `RawDocument` contract.
- Future write actions are unsafe without explicit confirmation.
- Premature MCP integration can complicate the MVP before core services are stable.
- Sensitive data exposure remains a privacy risk if full text is logged by default.

## Validation

- Review risk mitigations during milestone planning and release checks.
- Verify future features remain outside MVP unless [goals-and-scope.md](goals-and-scope.md) is explicitly updated.
- Verify future connector designs normalize into the same internal contracts.
- Verify any future destructive action requires explicit confirmation.

## Update rules

- Update this file when risks, mitigations, or future requirements change.
- Update [goals-and-scope.md](goals-and-scope.md) when a future requirement moves into MVP scope.
- Update [release-plan.md](release-plan.md) when future work becomes an active milestone.
