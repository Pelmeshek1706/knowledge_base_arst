---
name: tech-lead-documentation
description: 'Use when creating or updating documentation for the personal_kb project, especially README.md, architecture docs, ADRs, roadmap docs, developer handoffs, QA process docs, and documentation summaries.'
---

# Tech Lead Documentation Skill

## Purpose

Create documentation that accurately describes the `personal_kb` project and helps humans, coding agents, QA agents, and future maintainers understand the system.

This skill is for documentation only. Do not implement production code.

## Required Role

Before executing, read:

- `.codex/agents/ai-ml-tech-lead-docs.toml`

Apply that role as the active behavior for this task.

## Allowed Write Paths

- `README.md`
- `AGENTS.md`
- `docs/`
- `.codex/`
- `.codex/prompts/`
- `.codex/skills/`
- `.codex/handoffs/`
- `.codex/qa_reports/`

Do not modify by default:

- `src/`
- `tests/`
- `configs/`
- `scripts/`
- `pyproject.toml`
- lock files

## Required Documentation Rule

Any documentation of the agentic workflow must include:

- Tech Lead plans first.
- User approval is required before Python Engineer starts implementation.
- Python Engineer executes exactly one task at a time.
- QA reviews exactly one completed task at a time.
- No automatic continuation to the next task.

## Required Reading Before README Work

Read or inspect:

1. `README.md`
2. `AGENTS.md`
3. `docs/index.md`
4. `docs/architecture/index.md`
5. `docs/architecture/overview.md`
6. `docs/implementation/repository-structure.md`
7. `docs/roadmap/index.md`
8. `pyproject.toml`
9. top-level repository tree

If a file does not exist, mention it in the final summary.

## README Structure

Use this structure by default:

```markdown
# personal_kb

## Overview

## What This Project Does

## MVP Scope

## Non-Goals

## Architecture Summary

## Repository Structure

## Requirements

## Setup

## Configuration

## CLI Usage

## Development Workflow

## Agentic Development Workflow

## Testing and Validation

## Documentation Map

## Current Roadmap

## Risks / Limitations

## License
```

## Documentation Quality Rules

Each document must answer:

- What changed?
- Why does it matter?
- What components are affected?
- What is explicitly out of scope?
- What should the Developer Agent do next?
- How should QA validate it?
- Does this require a new ADR?

## Final Output

```text
Documentation Updated:
- ...

Reason:
- ...

Implementation Impact:
- ...

Developer Next Steps:
- ...

QA Validation:
- ...
```
