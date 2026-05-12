Use the `tech-lead-documentation` skill.

Act as `ai_ml_tech_lead_docs`.

Read:
- `.codex/agents/ai-ml-tech-lead-docs.toml`
- `.codex/skills/tech-lead-documentation/SKILL.md`
- `AGENTS.md`
- `README.md`
- `docs/`
- `pyproject.toml`

Task:
<DOCUMENTATION_TASK>

Rules:
- documentation only;
- do not modify `src/`, `tests/`, `configs/`, `scripts/`, `pyproject.toml`, or lock files;
- do not invent features;
- mark missing information as TODO.
