# personal_kb Codex Agentic Setup

This `.codex` setup defines project-specific roles, skills, prompts, handoff contracts, and QA/reporting folders for the `personal_kb` project.

## Roles

| Role | File | Responsibility |
|---|---|---|
| AI/ML Tech Lead | `agents/ai-ml-tech-lead.toml` | Planning, task decomposition, developer handoff after user approval |
| AI/ML Tech Lead Architect | `agents/ai-ml-tech-lead-architect.toml` | High-reasoning architecture decisions, ADR-level design, difficult trade-offs |
| AI/ML Tech Lead Docs | `agents/ai-ml-tech-lead-docs.toml` | Documentation-only writing and maintenance |
| AI/ML Python Engineer | `agents/ai-ml-python-engineer.toml` | Implementation of exactly one approved task at a time |
| AI/ML QA Engineer | `agents/ai-ml-qa-engineer.toml` | QA review of exactly one completed developer task at a time |

## Mandatory Workflow

```text
User request
  → Tech Lead plan
  → User approval required
  → Tech Lead hands off exactly one task
  → Python Engineer implements exactly one task
  → QA Engineer reviews exactly one task
  → Python Engineer fixes QA bug reports if needed
  → QA verifies
  → Final report
  → User/Tech Lead approval required before next task
```

## Critical Rules

- Tech Lead must not request Python Engineer implementation before explicit user approval.
- Python Engineer must execute exactly one approved task per run.
- QA must review exactly one completed developer task per run.
- No agent may automatically continue to the next task.
- Every implementation task must pass through QA before the next implementation task starts.

## Practical Use in Codex App / CLI

If `.codex/agents/*.toml` are not visible as selectable agents, use them as role files:

```text
Use the `<skill-name>` skill.
Act as `<agent-name>`.
Read `.codex/agents/<agent-file>.toml` before executing.
Then perform the task.
```

Example:

```text
Use the `tech-lead-planning` skill.
Act as `ai_ml_tech_lead`.
Read `.codex/agents/ai-ml-tech-lead.toml`.
Plan the work only. Do not invoke Python Engineer until I approve the plan.
```

## Model Notes

Some model IDs in these files reflect desired model choices. If your Codex runtime does not support a requested model ID, replace it with a supported Codex model in your environment, such as an available GPT Codex model.
