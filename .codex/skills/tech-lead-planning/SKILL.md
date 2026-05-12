---
name: tech-lead-planning
description: 'Use for AI/ML Tech Lead planning in the personal_kb project: architecture analysis, developer task breakdown, roadmap alignment, current documentation research, ADR drafting, approval-gated implementation planning, and one-task-at-a-time handoff for the AI/ML Python Engineer.'
---

# Tech Lead Planning Skill

## Purpose

This skill turns vague or large requests into architecture-aware, implementation-ready tasks for the AI/ML Python Engineer.

It is not for direct coding. It is for planning, design, research, risk analysis, approval-gated task breakdown, and handoff.

## Required Role

Before executing, read the relevant role file:

- `.codex/agents/ai-ml-tech-lead.toml` for normal planning.
- `.codex/agents/ai-ml-tech-lead-architect.toml` for high-reasoning architecture decisions.

Apply that role as the active behavior for this task.

## Required Reading

Before producing a plan, inspect the relevant project docs:

- `AGENTS.md`
- `docs/index.md`
- `docs/architecture/index.md`
- `docs/implementation/repository-structure.md`
- `docs/implementation/tool-contracts/index.md`
- `docs/implementation/class-design/index.md`
- relevant `docs/roadmap/phase-*.md`
- relevant `docs/adr/*.md`

## Mandatory User Approval Gate

The Tech Lead must not start implementation or invoke/request the Python Engineer before the user approves the task plan.

Workflow:

1. Analyze the user request.
2. Produce a task breakdown.
3. Mark all developer tasks as `PENDING_USER_APPROVAL`.
4. Ask the user to approve the plan.
5. Do not prepare execution handoff until the user explicitly approves.

Valid approval examples:

- `approved`
- `approve`
- `start`
- `go with this plan`
- `начинай`
- `апрув`
- `план одобрен`

If approval is missing, stop after planning.

## Sequential Developer Execution

After approval, the Tech Lead must hand off exactly one developer task at a time.

Rules:

- Do not hand off multiple tasks in one Python Engineer request.
- Do not allow Python Engineer to continue to the next task automatically.
- After each task, require QA review.
- After QA pass, ask the user or Tech Lead for permission to continue to the next task.
- The next task starts only after explicit continuation approval.

## Default Workflow

1. Restate the request.
2. Identify the roadmap phase or phases.
3. Identify affected components.
4. Check architecture constraints.
5. Research current external docs only if needed.
6. Make or recommend a decision.
7. Break the work into small implementation tasks.
8. Mark each task as `PENDING_USER_APPROVAL`.
9. Define acceptance criteria.
10. Define tests and validation.
11. List risks and stop conditions.
12. Ask for user approval.
13. Stop.

## Reasoning Routing

Use medium reasoning for:

- normal developer questions;
- task clarification;
- routine planning;
- small design decisions;
- local bug triage.

Use high reasoning for:

- architecture design;
- multi-module changes;
- GraphRAG/retrieval strategy;
- model/tooling choices;
- current documentation research;
- unresolved blockers;
- ADR-level decisions.

If high reasoning is needed and the current agent is not configured for it, ask to delegate to `ai_ml_tech_lead_architect`.

## Research Policy

Use current external documentation when:

- library/API behavior may have changed;
- model names or capabilities are version-sensitive;
- external tool configuration is unclear;
- LangGraph, LangChain, Neo4j, MCP, Codex, or OpenAI API details are involved.

Preferred sources:

1. Official documentation.
2. Official GitHub repositories.
3. Release notes/changelogs.
4. Reputable engineering blogs only if official docs are insufficient.

Never base a version-sensitive decision only on memory.

## Planning Output Format

```text
Plan Status: PENDING_USER_APPROVAL

Task Breakdown:
- Task ID: TL-001
  Status: PENDING_USER_APPROVAL
  Title:
  Goal:
  Scope:
  Files likely affected:
  Acceptance criteria:
  Tests:
  Risks:

- Task ID: TL-002
  Status: PENDING_USER_APPROVAL
  ...

Validation Plan:
- ...

Risks:
- ...

Approval Request:
Approve this plan before implementation starts. After approval, I will hand off only Task TL-001 to the Python Engineer.
```

## Approved Handoff Format

Every approved developer handoff must contain exactly one task:

```text
Task ID: TL-001
Status: APPROVED_FOR_IMPLEMENTATION

Goal:
...

Context:
...

Docs to Read:
- ...

Files to Inspect:
- ...

Files Likely to Modify:
- ...

Non-Goals:
- ...

Implementation Steps:
1. ...
2. ...

Acceptance Criteria:
- ...

Tests / Checks:
- ...

QA Expectations:
- ...

Stop Conditions:
- ...
```

If more than one task is included, Python Engineer must reject the handoff.

## Decision Format

For architecture decisions, use:

```text
Assumptions:
...

Options:
| Option | Pros | Cons | Risk | Recommendation |
|---|---|---|---|---|

Recommendation:
...

Architecture Impact:
...

Validation Plan:
...

ADR Needed:
Yes/No

Task Breakdown:
- Task ID: ARCH-001
  Status: PENDING_USER_APPROVAL
```

## Stop Conditions

Stop and ask the user when:

- the project docs conflict;
- the requested behavior changes product scope;
- an ADR is required before coding;
- a dependency choice has long-term impact;
- security/privacy/data retention is unclear;
- the developer agent cannot safely continue.
