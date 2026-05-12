Use the `ai-ml-quality-assurance` skill.

Act as `ai_ml_qa_engineer`.

Read:
- `.codex/agents/ai-ml-qa-engineer.toml`
- `.codex/skills/ai-ml-quality-assurance/SKILL.md`

Review exactly one completed implementation task.

Inputs:
- Task ID: <TASK_ID>
- Original task: <TASK>
- Roadmap phase: <PHASE>
- Developer summary: <SUMMARY>
- Changed files: <FILES>
- Tests/checks run: <COMMANDS_AND_RESULTS>

Return:
- QA result;
- separate bug reports for each issue;
- validation commands run;
- fix requests for developer;
- final report draft.
