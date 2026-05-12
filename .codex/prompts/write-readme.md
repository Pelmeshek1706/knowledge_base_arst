Use `ai_ml_tech_lead_docs` with the `tech-lead-documentation` skill.

Task:
Create or update the root `README.md` for the `personal_kb` project.

Rules:
- Documentation only.
- Do not modify `src/`, `tests/`, `configs/`, `scripts/`, `pyproject.toml`, or lock files.
- Use existing project docs and repository structure as source of truth.
- Do not invent features.
- Separate implemented MVP scope from planned/future work.
- If information is missing, mark it as TODO or list it under Missing Information.
- Include the approval-gated agentic development workflow.

Read before writing:
- `AGENTS.md`
- existing `README.md`
- `docs/index.md`
- `docs/architecture/index.md`
- `docs/architecture/overview.md`
- `docs/implementation/repository-structure.md`
- `docs/roadmap/index.md`
- `docs/adr/index.md`
- `pyproject.toml`
- repository tree

README must include:
1. Overview
2. What This Project Does
3. MVP Scope
4. Non-Goals
5. Architecture Summary
6. Repository Structure
7. Requirements
8. Setup
9. Configuration
10. CLI Usage
11. Development Workflow
12. Agentic Development Workflow
13. Testing and Validation
14. Documentation Map
15. Current Roadmap
16. Risks / Limitations
17. License

After writing, return:
- files changed;
- key sections added/updated;
- assumptions;
- missing information;
- suggested follow-up documentation tasks.
