# Single Task Policy

The AI/ML Python Engineer must execute exactly one task per run.

## Required Handoff

```text
Task ID: TL-001
Status: APPROVED_FOR_IMPLEMENTATION
```

## Reject Handoff If

- more than one task ID is present;
- status is not `APPROVED_FOR_IMPLEMENTATION`;
- user approval is not mentioned;
- acceptance criteria are missing;
- tests/checks are missing.

## Completion

After completing the task:

1. prepare QA handoff;
2. stop;
3. do not start the next task.
