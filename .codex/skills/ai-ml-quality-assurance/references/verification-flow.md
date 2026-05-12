# Verification Flow

1. Receive exactly one completed task.
2. Confirm task ID and READY_FOR_QA status.
3. Inspect changed files.
4. Run relevant tests/checks where safe.
5. Review architecture/product fit.
6. Review LLM/RAG behavior where relevant.
7. Produce QA result.
8. If failed, create separate bug reports.
9. If fixes are submitted, verify only those fixes for the same task.
10. Return control to Tech Lead/user. Do not start next task.
