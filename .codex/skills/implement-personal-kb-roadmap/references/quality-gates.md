# Quality Gates

Run the narrowest relevant checks first.

## Common Commands

```bash
uv run pytest tests/<relevant_test_file>.py -q
```

If project-wide tests are stable:

```bash
uv run pytest -q
```

If configured:

```bash
uv run ruff check .
uv run mypy src
```

## Required Final Summary

- task ID;
- changed files;
- behavior changed;
- tests/checks run;
- known risks;
- QA handoff;
- explicit stop before next task.
