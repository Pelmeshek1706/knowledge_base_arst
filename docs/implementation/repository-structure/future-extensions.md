# Future Extensions

## Purpose

This file preserves reserved future extension locations and constraints from the repository-structure document.

## When to read this

Read this before adding MCP, API, external connector, or FAQ/QA memory packages.

## Related files

- [tools-agent-adapters.md](tools-agent-adapters.md)
- [package-boundaries-and-import-rules.md](package-boundaries-and-import-rules.md)
- [../tool-contracts/future-mcp-adapter.md](../tool-contracts/future-mcp-adapter.md)
- [../../architecture/agent-design.md](../../architecture/agent-design.md)

## Source of truth

This file is authoritative for repository locations reserved for non-MVP extensions. Current MCP behavior and constraints are owned by the tool-contracts future MCP adapter document.

## Content

### MCP server adapter

Location:

```text
personal_kb/adapters/mcp/
```

Future command:

```bash
kb serve-mcp
```

Not MVP primary path.

### FastAPI adapter

Location:

```text
personal_kb/adapters/api/
```

Future command:

```bash
kb serve-api
```

### External connectors

Future location:

```text
personal_kb/connectors/
  confluence.py
  jira.py
  gmail.py
  google_drive.py
```

Not included in MVP because MVP source is local files.

### FAQ/QA memory

Future location:

```text
personal_kb/memory/
  faq_store.py
  qa_memory_service.py
```

Not included in MVP.

## Dependencies

- `personal_kb/adapters/mcp/`
- `personal_kb/adapters/api/`
- `personal_kb/connectors/`
- `personal_kb/memory/`
- `personal_kb/tools/knowledge_tool_service.py`

## Failure modes / risks

- Future adapters can duplicate core tool logic instead of using `KnowledgeToolService`.
- Connectors can expand scope beyond local files before MVP is stable.
- FAQ/QA memory can blur source-grounded Q&A if not separated from document citations.
- MCP can become the primary internal path before the MVP service facade is stable.

## Validation

- Confirm MCP/API adapters call the existing service facade instead of duplicating business logic.
- Confirm external connectors are not added to the MVP local-file ingestion path without an explicit design update.
- Confirm future memory features preserve source-grounding and citation behavior.

## Update rules

Update this file when reserved extension locations, future commands, MVP exclusions, or adapter/connector constraints change.
