# Validation

This package was regenerated after fixing invalid YAML frontmatter in `SKILL.md` files.

Rules applied:

- Every `SKILL.md` starts with YAML frontmatter fenced by `---`.
- Frontmatter contains only `name` and `description`.
- `description` values are quoted to avoid YAML parser errors caused by colons.
- Tech Lead agents use `model = "gpt-5.4"` and `model_reasoning_effort = "high"`.
- Python Engineer and QA agents use `model = "gpt-5.4-mini"` and `model_reasoning_effort = "medium"`.

Validated with local YAML and TOML parsers before packaging.
