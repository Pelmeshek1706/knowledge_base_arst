# Package Boundaries And Import Rules

## Purpose

This file defines the package dependency direction, layer boundaries, and allowed/forbidden import patterns for `personal_kb`.

## When to read this

Read this before adding imports across package layers, moving business logic between modules, or creating new framework adapters.

## Related files

- [overview.md](overview.md)
- [tools-agent-adapters.md](tools-agent-adapters.md)
- [../class-design/index.md](../class-design/index.md)
- [../tool-contracts/index.md](../tool-contracts/index.md)

## Source of truth

This file is authoritative for repository-level dependency direction and import rules.

## Content

`personal_kb/` is the main Python package.

### Design rule

```text
Framework adapters depend on services.
Services depend on repositories/clients/schemas.
Core modules and schemas do not depend on framework adapters.
```

Allowed dependency direction:

```text
cli / adapters / agent
-> tools
-> services
-> graph / storage / models / retrieval / qa
-> schemas / core
```

Forbidden dependency direction:

```text
schemas -> services
core -> cli
storage -> cli
graph -> agent
models -> tools
services -> langgraph nodes
```

### Allowed imports

```python
# CLI can call services/tools
from personal_kb.tools.knowledge_tool_service import KnowledgeToolService

# Services can call graph/storage/models
from personal_kb.graph.graph_service import GraphService
from personal_kb.storage.manifest_store import ManifestStore

# Any layer can import schemas
from personal_kb.schemas.search import SearchDocumentsRequest
```

### Forbidden imports and behavior

```python
# Core must not depend on CLI
from personal_kb.cli.main import main

# Storage must not call LangGraph
from personal_kb.agent.graph import build_agent

# Tools must not implement Cypher directly
neo4j_driver.execute_query("MATCH ...")

# LangGraph nodes must not parse files
PdfParser().parse(path)
```

## Dependencies

- `personal_kb/core/`
- `personal_kb/schemas/`
- `personal_kb/storage/`
- `personal_kb/graph/`
- `personal_kb/retrieval/`
- `personal_kb/qa/`
- `personal_kb/tools/`
- `personal_kb/agent/`
- `personal_kb/adapters/`
- `personal_kb/cli/`

## Failure modes / risks

- Cypher logic can leak into tools instead of staying behind graph services.
- LangGraph nodes can accumulate business logic that belongs in services.
- Storage can become coupled to CLI or agent runtime.
- Core and schemas can stop being reusable if they depend on adapters or services.

## Validation

- Review new imports against the allowed dependency direction.
- Confirm CLI handlers parse arguments and call services/tools only.
- Confirm LangGraph nodes orchestrate service/tool calls only.
- Confirm framework-specific code lives under `personal_kb/adapters/` or agent integration modules.

## Update rules

Update this file when package layers are added, dependency direction changes, imports become allowed/forbidden, or adapter boundaries change.
