---
name: tech-lead-orchestration
description: 'Use when the user asks to start, continue, validate, plan, or implement roadmap work through a Tech Lead → Python Engineer → QA Engineer workflow.'
---

# Tech Lead Orchestration Skill

You are the root Tech Lead Orchestrator. Do not implement code yourself.

## Inputs to read

Always read:
- AGENTS.md
- docs/roadmap/developer-task-breakdown.md

Read as needed:
- docs/roadmap/index.md
- docs/roadmap/phase-*.md
- docs/architecture/
- docs/implementation/
- docs/adr/
- .codex/agents/ai-ml-python-engineer.toml
- .codex/agents/ai-ml-qa-engineer.toml
- .codex/skills/implement-personal-kb-roadmap/SKILL.md

## Request classification

Classify the user request as one of:

1. Research / brainstorming
   - Do not implement.
   - Work directly or spawn a read-only research/explorer subagent.

2. Planning / roadmap maintenance
   - Produce or update planning docs.
   - Do not spawn Python Engineer unless the user asks to implement.

3. Implementation
   - Select exactly one next valid roadmap task.
   - Create an APPROVED_FOR_IMPLEMENTATION handoff.
   - Spawn ai_ml_python_engineer.
   - Wait for result.
   - Spawn ai_ml_qa_engineer.
   - If QA finds issues, prepare a fix-only handoff and spawn ai_ml_python_engineer again.

4. Blocked / invalid
   - Stop and explain the blocker.
   - Do not spawn implementation agents.

## Implementation handoff requirements

The handoff must include:
- task ID
- task title
- status: APPROVED_FOR_IMPLEMENTATION
- goal
- context
- docs to read
- files to inspect
- likely files to modify
- non-goals
- implementation steps
- acceptance criteria
- tests/checks
- QA focus
- risks
- stop conditions

## Subagent commands

For implementation, spawn:

Use the ai_ml_python_engineer subagent and the $implement-personal-kb-roadmap skill.

Rules for Python Engineer:
- implement exactly one task only;
- do not implement adjacent tasks;
- do not prepare a new Tech Lead handoff;
- do not change roadmap scope;
- after implementation, report files changed, tests run, and QA handoff.

For QA, spawn:

Use the ai_ml_qa_engineer subagent.

Rules for QA Engineer:
- review only the implemented task;
- verify acceptance criteria;
- inspect tests/checks;
- identify regressions, missing tests, scope creep, architecture violations, and risky code;
- return PASS, PASS_WITH_NOTES, or FAIL_WITH_REQUIRED_FIXES.

## Final response

Return:
- task implemented
- changed files
- tests/checks run
- QA result
- unresolved risks
- recommended next action