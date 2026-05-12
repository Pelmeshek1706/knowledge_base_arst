# Recommended AGENTS.md Snippet

Add this to the root `AGENTS.md` if you want project-level Codex behavior to consistently follow the approval-gated agentic workflow.

## Agentic Development Workflow

For implementation work, use the approval-gated workflow:

1. AI/ML Tech Lead analyzes the user request and produces a task plan.
2. User must explicitly approve the task plan before implementation starts.
3. AI/ML Tech Lead hands off exactly one approved task to AI/ML Python Engineer.
4. AI/ML Python Engineer implements exactly one task and stops.
5. AI/ML QA Engineer reviews exactly one completed task.
6. AI/ML Python Engineer fixes QA issues one at a time.
7. AI/ML QA Engineer verifies fixes.
8. No next task starts automatically.

Explicit approval examples:

- `approved`
- `approve`
- `start`
- `go with this plan`
- `начинай`
- `апрув`
- `план одобрен`

If approval is missing, do not start implementation.
