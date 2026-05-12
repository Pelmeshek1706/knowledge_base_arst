# Developer Handoff Contract

## Status Values

Every task must have one of:

- `PENDING_USER_APPROVAL`
- `APPROVED_FOR_IMPLEMENTATION`
- `IN_PROGRESS`
- `READY_FOR_QA`
- `QA_FAILED`
- `QA_PASSED`
- `DONE`

## Tech Lead Planning Output

```text
Plan Status: PENDING_USER_APPROVAL

Tasks:
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
```

The Tech Lead must stop after this and ask for user approval.

## Python Engineer Handoff

Only one task is allowed:

```text
Task ID: TL-001
Status: APPROVED_FOR_IMPLEMENTATION

Goal:
...

Scope:
...

Files to inspect:
...

Files likely to modify:
...

Non-goals:
...

Implementation steps:
1. ...
2. ...

Acceptance criteria:
- ...

Tests/checks:
- ...

QA expectations:
- ...

Stop conditions:
- ...
```

If more than one task is included, the Python Engineer must stop and request a single-task handoff.

## QA Handoff

Only one completed task is allowed:

```text
Task ID: TL-001
Status: READY_FOR_QA

Original task:
...

Changed files:
- ...

Tests/checks run:
- ...

Known risks:
- ...

Recommended QA focus:
- ...
```
