from __future__ import annotations

import builtins
import importlib
import sys
from types import ModuleType


def test_model_modules_import_without_loading_optional_runtime_packages(
    monkeypatch,
) -> None:
    blocked_prefixes = ("sentence_transformers", "openai")
    real_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"unexpected optional import: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    for module_name in [
        "personal_kb.models",
        "personal_kb.models.embedding_client",
        "personal_kb.models.llm_client",
        "personal_kb.models.reranker_client",
        "personal_kb.models.structured_extraction_client",
    ]:
        sys.modules.pop(module_name, None)
        module = importlib.import_module(module_name)
        assert module is not None
