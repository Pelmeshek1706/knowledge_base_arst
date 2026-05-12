# Phase 12: CLI Integration

## Purpose

Provide a usable developer interface over setup, ingestion, search, Q&A, and
status.

## Status

Draft roadmap phase. Priority: P0.

## Depends on

- [Phase 11: LangGraph Agent](phase-11-langgraph-agent.md)

## Outputs

```text
personal_kb/cli/
  main.py
  commands.py
  formatters.py
```

## In scope

- CLI entrypoint and command wiring.
- CLI formatters.
- Setup, ingestion, search, ask, related, duplicates, and status commands.
- Human-readable output by default.
- `--json` structured output.
- Reuse of the same services/tools as the agent for search and ask.

## Out of scope

- Web UI.
- Telegram bot.
- External system write actions.

## Related docs

- [Roadmap index](index.md)
- [Phase 13: Benchmark + Evaluation](phase-13-benchmark-evaluation.md)

## Source of truth

This file is authoritative for Phase 12 CLI command and output behavior
roadmap scope.

## Implementation checklist

Commands:

```bash
kb setup-db
kb ingest data
kb search "accounting budget"
kb ask "Where is information about WP2?"
kb related --doc-id <uuid>
kb duplicates
kb status
```

Output behavior:

- Human-readable output by default.
- `--json` flag for structured output.
- Search and ask commands use the same services/tools as the agent.

## Exit criteria

- CLI works from a fresh project checkout.
- CLI returns helpful errors for missing Neo4j schema.
- `kb ingest data` automatically syncs Neo4j after successful processing.
- `kb search` and `kb ask` can run against processed test data.

## Validation

- Run CLI commands from a fresh project checkout.
- Trigger missing-Neo4j-schema behavior and confirm helpful errors.
- Run `kb ingest data` and confirm Neo4j sync after successful processing.
- Run `kb search` and `kb ask` against processed test data.
- Confirm `--json` returns structured output.

## Failure modes / risks

- CLI commands must use the same services/tools as the agent for search and
  ask, or behavior can drift.
- Missing Neo4j schema must produce helpful errors rather than obscure stack
  traces.

## Update rules

Update this file when CLI commands, output behavior, service/tool reuse rules,
or CLI acceptance criteria change.
