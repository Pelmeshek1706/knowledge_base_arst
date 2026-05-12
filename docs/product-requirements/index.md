# Product Requirements Index

## Purpose

This documentation folder defines the Product Requirements source of truth for the `personal_kb` local-first GraphRAG system.

## When to read this

Start from this folder for:

- product scope changes;
- MVP behavior changes;
- functional requirement updates;
- search, Q&A, CLI, agent-tool, or MCP-boundary changes;
- validation, benchmark, and acceptance planning;
- release planning;
- future requirement review.

## Source of truth

- [overview.md](overview.md) is authoritative for the product summary, problem statement, and final MVP definition.
- [goals-and-scope.md](goals-and-scope.md) is authoritative for product goals, MVP scope, and non-goals.
- [users-and-stories.md](users-and-stories.md) is authoritative for personas, user stories, priorities, and acceptance criteria.
- [functional-requirements.md](functional-requirements.md) is authoritative for ingestion, parsing, chunking, extraction, model, storage, and graph-sync requirements.
- [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md) is authoritative for search, Q&A, CLI, agent tooling, and future MCP adapter requirements.
- [non-functional-requirements.md](non-functional-requirements.md) is authoritative for cross-cutting quality attributes and safety constraints.
- [data-and-graph-requirements.md](data-and-graph-requirements.md) is authoritative for manifest, processed JSON, chunk data, graph nodes, relationships, and deterministic `RELATED_TO` rules.
- [validation-and-acceptance.md](validation-and-acceptance.md) is authoritative for benchmark data, metrics, and MVP acceptance criteria.
- [release-plan.md](release-plan.md) is authoritative for product milestone sequencing and milestone exit criteria.
- [risks-and-future-requirements.md](risks-and-future-requirements.md) is authoritative for product risks, mitigations, and future requirements.
- [dependencies-open-questions-traceability.md](dependencies-open-questions-traceability.md) is authoritative for dependencies, open product questions, and PRD-to-architecture traceability.

## Reading order

1. Read [overview.md](overview.md) for the product summary and final MVP definition.
2. Read [goals-and-scope.md](goals-and-scope.md) before changing what is in or out of MVP.
3. Read the focused file related to the current task.
4. Read related files listed in the focused document.
5. Do not scan the whole folder unless explicitly requested.

## Files

| Topic | File | Purpose |
|---|---|---|
| Overview | [overview.md](overview.md) | Explains the product summary, problem statement, and final MVP definition. |
| Goals and scope | [goals-and-scope.md](goals-and-scope.md) | Defines product goals, MVP scope, and non-goals. |
| Users and stories | [users-and-stories.md](users-and-stories.md) | Defines personas, user stories, priorities, and acceptance criteria. |
| Functional requirements | [functional-requirements.md](functional-requirements.md) | Defines ingestion, parsing, chunking, extraction, model, storage, and graph-sync requirements. |
| Search, Q&A, CLI, and agent requirements | [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md) | Defines query behavior, CLI behavior, tool requirements, output contracts, and MCP adapter constraints. |
| Non-functional requirements | [non-functional-requirements.md](non-functional-requirements.md) | Defines cross-cutting quality, safety, privacy, and portability requirements. |
| Data and graph requirements | [data-and-graph-requirements.md](data-and-graph-requirements.md) | Defines data contracts, graph nodes, relationships, and deterministic relationship rules. |
| Validation and acceptance | [validation-and-acceptance.md](validation-and-acceptance.md) | Defines benchmark data, retrieval/Q&A/system metrics, and MVP acceptance criteria. |
| Release plan | [release-plan.md](release-plan.md) | Defines MVP milestone sequence, scope, and exit criteria. |
| Risks and future requirements | [risks-and-future-requirements.md](risks-and-future-requirements.md) | Preserves product risks, mitigations, and future requirements. |
| Dependencies, open questions, and traceability | [dependencies-open-questions-traceability.md](dependencies-open-questions-traceability.md) | Lists dependencies, unresolved product questions, and PRD-to-architecture mapping. |

## Update rules

- Update [goals-and-scope.md](goals-and-scope.md) when product goals, MVP scope, or non-goals change.
- Update [functional-requirements.md](functional-requirements.md) when ingestion, parsing, chunking, extraction, model execution, processed storage, or graph sync behavior changes.
- Update [search-qa-cli-agent-requirements.md](search-qa-cli-agent-requirements.md) when query behavior, CLI commands, agent tools, schemas, or MCP adapter boundaries change.
- Update [data-and-graph-requirements.md](data-and-graph-requirements.md) when storage contracts or graph schema requirements change.
- Update [validation-and-acceptance.md](validation-and-acceptance.md) when benchmarks, metrics, or release gates change.
- Update [release-plan.md](release-plan.md) when milestone order, scope, or exit criteria change.
- Update [dependencies-open-questions-traceability.md](dependencies-open-questions-traceability.md) when dependencies, open questions, or architecture mappings change.
- Keep risks, warnings, validation requirements, and failure modes in the focused file that owns them.

## Do not read everything by default

Coding agents should open only the focused files needed for the current task.
