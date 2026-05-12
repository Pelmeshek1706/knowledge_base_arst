# Code Review Checklist

- Single assigned task only.
- No unrelated refactoring.
- Type hints present.
- Pydantic used for boundary schemas.
- No business logic inside tool wrappers.
- No runtime agent control over ingestion/rebuild/sync/delete/write.
- Tests cover changed behavior.
- Failure modes handled.
- Logging/errors are useful.
- Public behavior documented if changed.
