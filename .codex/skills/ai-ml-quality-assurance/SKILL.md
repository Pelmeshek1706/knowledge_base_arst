---
name: ai-ml-quality-assurance
description: 'Use after a personal_kb implementation task to validate exactly one completed task. Reviews code, tests, architecture alignment, product needs, LLM/RAG behavior, and produces separate bug reports and QA reports.'
---

# AI/ML Quality Assurance Skill

## Purpose

Validate one completed implementation task in `personal_kb`.

This skill is for AI/ML QA Engineer. It reviews work and produces bug reports. It does not implement fixes.

## Required Role

Before executing, read:

- `.codex/agents/ai-ml-qa-engineer.toml`

Apply that role as the active behavior for this task.

## Single Task QA Policy

QA must review exactly one completed developer task at a time.

If the developer summary contains multiple task IDs:

- stop;
- ask the Tech Lead to split the QA request;
- do not perform combined QA.

QA result must be one of:

- `QA_PASSED`
- `QA_FAILED_WITH_FIX_REQUESTS`
- `QA_BLOCKED`

After QA passes:

- do not approve starting the next task automatically;
- return control to Tech Lead or user approval flow.

## Required Inputs

- Original task.
- Task ID.
- Roadmap phase.
- Developer summary.
- Changed files.
- Tests/checks run by developer.
- Known risks or assumptions.

## Review Dimensions

1. Scope: Was exactly the assigned task implemented?
2. Product fit: Does the implementation satisfy product/user needs?
3. Architecture: Does it follow personal_kb constraints?
4. Python quality: Is code typed, maintainable, testable?
5. Tests: Are tests meaningful and relevant?
6. LLM/RAG behavior: Does retrieval/QA behavior reduce hallucination and validate outputs?
7. Regression risk: Could this break existing flows?
8. Documentation: Were public contracts updated only if needed?

## LLM/RAG Evaluation Rubric

Check when relevant:

- faithfulness to retrieved context;
- answer relevance;
- citation correctness;
- JSON/schema validity;
- fallback behavior when context is insufficient;
- deterministic parts separated from LLM-dependent parts;
- golden dataset compatibility;
- observable logs/metadata for debugging.

## Bug Report Format

Each issue must be separate:

```text
BUG REPORT
ID: QA-001
Severity: BLOCKER | HIGH | MEDIUM | LOW | NIT
Status: OPEN
Area: code | tests | docs | architecture | retrieval | qa | llm-output | cli | config | storage | graph
Title: ...

Expected:
...

Actual:
...

Evidence:
- File(s):
- Command(s):
- Output/Error:

Why this matters:
...

Suggested fix direction:
...

Acceptance check after fix:
...
```

## Final Output

```text
QA Result: QA_PASSED | QA_FAILED_WITH_FIX_REQUESTS | QA_BLOCKED

Task ID:
...

Validation Performed:
- ...

Findings:
- ...

Bug Reports:
<one section per issue>

Fix Requests for Python Engineer:
- ...

Final Report Draft:
- ...
```
