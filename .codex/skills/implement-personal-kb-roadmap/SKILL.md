---
name: implement-personal-kb-roadmap
description: 'Use for implementation, refactoring, testing, and debugging tasks in the personal_kb GraphRAG project. This skill is only for the AI/ML Python Engineer and only after Tech Lead produced a user-approved single-task handoff.'
---

# Implement Personal KB Roadmap Skill

## Purpose

Implement one approved `personal_kb` roadmap task safely and consistently.

This skill is for the AI/ML Python Engineer only.

## Required Role

Before executing, read:

- `.codex/agents/ai-ml-python-engineer.toml`

Apply that role as the active behavior for this task.

## Hard Preconditions

Implementation may start only if all are true:

1. A Tech Lead handoff exists.
2. The handoff contains exactly one task ID.
3. The task status is `APPROVED_FOR_IMPLEMENTATION`.
4. User approval happened before the handoff.
5. The task includes acceptance criteria and tests/checks.

If any condition is missing, stop and ask Tech Lead for a valid single-task approved handoff.

## Single Task Execution Rule

Execute exactly one task.

Forbidden:

- implementing multiple task IDs;
- moving to next roadmap phase;
- opportunistic refactoring;
- unrelated bug fixes;
- starting the next task after finishing current task.

After implementation, produce QA handoff and stop.

## Required Reading Before Coding

Before modifying files, inspect:

- `AGENTS.md`
- relevant `docs/roadmap/phase-*.md`
- `docs/architecture/overview.md`
- `docs/implementation/repository-structure.md`
- relevant class/tool contract docs
- existing code and tests for the assigned task only

## Core Architecture Rules

- Runtime agent access must go through search/Q&A tools only.
- LangChain `StructuredTool` wrappers must stay thin.
- `KnowledgeToolService` is the facade for tool-facing operations.
- Business logic belongs in services, not tools.
- Deterministic ingestion must not be controlled by the LangGraph agent.
- `kb_storage` processed JSON remains the primary processed source of truth.
- Neo4j is used for graph/vector search and relationships.
- MCP adapter is future-facing, not the MVP internal path.

## Implementation Workflow

1. Validate single-task approved handoff.
2. Restate the assigned task ID and goal.
3. Identify affected roadmap phase.
4. Identify affected modules.
5. Inspect existing interfaces before creating new abstractions.
6. Make the smallest coherent implementation.
7. Add or update tests.
8. Run the narrowest relevant checks first.
9. If those pass, run broader checks if available.
10. Prepare QA handoff.
11. Stop.

## Completion Output

```text
Task ID:
...

Summary:
- ...

Files Changed:
- ...

Validation:
- ...

Risks:
- ...

QA Handoff:
- Original task:
- Roadmap phase:
- Changed files:
- Tests/checks run:
- Known risks:
- Recommended QA focus:

Next:
Send this task to AI/ML QA Engineer. Do not start the next task.
```

## Blocking Escalation Protocol

Stop and ask when:

- the task contains multiple task IDs;
- approval status is missing;
- the task conflicts with existing documentation;
- the implementation requires a new architectural decision;
- a dependency/version choice is unclear;
- tests fail for a reason outside the current task;
- continuing would require guessing.

When blocked, return:

```text
BLOCKED

Task ID:
...

What I tried:
...

Error/context:
...

Likely cause:
...

Decision needed:
...

Safe options:
1. ...
2. ...
```
