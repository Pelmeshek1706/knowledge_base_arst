# Single Task QA Policy

QA reviews exactly one completed task at a time.

Reject QA request if:

- multiple task IDs are present;
- task ID is missing;
- developer summary is missing;
- changed files are missing;
- tests/checks are missing;
- task is not READY_FOR_QA.

After QA passes, no next task starts automatically.
