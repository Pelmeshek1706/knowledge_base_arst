from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
import os
from typing import cast

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from personal_kb.core.errors import ConfigError
from personal_kb.schemas.config import AppConfig

_DEFAULT_CONFIG_PATH = Path("configs/default.yaml")
_LEGACY_ENV_TO_PATHS: dict[str, tuple[str, ...]] = {
    "NEO4J_URI": ("neo4j", "uri"),
    "NEO4J_USER": ("neo4j", "username"),
    "NEO4J_USERNAME": ("neo4j", "username"),
    "NEO4J_PASSWORD": ("neo4j", "password"),
    "NEO4J_DATABASE": ("neo4j", "database"),
    "NEO4J_FALLBACK_DATABASE": ("neo4j", "fallback_database"),
    "LMSTUDIO_URL": ("models", "llm", "base_url"),
    "LMSTUDIO_MODEL": ("models", "llm", "model_name"),
    "LMSTUDIO_EMBED_MODEL": ("models", "embedding", "model_name"),
    "LOCAL_EMBED_DIMENSIONS": ("models", "embedding", "dimension"),
}
_PREFERRED_ENV_TO_PATHS: dict[str, tuple[str, ...]] = {
    "PERSONAL_KB_PROJECT_NAME": ("project", "name"),
    "PERSONAL_KB_CONFIG": ("project", "config_path"),
    "PERSONAL_KB_PATH_MODE": ("project", "path_mode"),
    "PERSONAL_KB_STORAGE_DATA_DIR": ("storage", "data_dir"),
    "PERSONAL_KB_STORAGE_KB_STORAGE_DIR": ("storage", "kb_storage_dir"),
    "PERSONAL_KB_STORAGE_BENCHMARK_DIR": ("storage", "benchmark_dir"),
    "PERSONAL_KB_NEO4J_URI": ("neo4j", "uri"),
    "PERSONAL_KB_NEO4J_USERNAME": ("neo4j", "username"),
    "PERSONAL_KB_NEO4J_PASSWORD": ("neo4j", "password"),
    "PERSONAL_KB_NEO4J_DATABASE": ("neo4j", "database"),
    "PERSONAL_KB_NEO4J_FALLBACK_DATABASE": ("neo4j", "fallback_database"),
    "PERSONAL_KB_MODEL_LLM_PROVIDER": ("models", "llm", "provider"),
    "PERSONAL_KB_MODEL_LLM_BASE_URL": ("models", "llm", "base_url"),
    "PERSONAL_KB_MODEL_LLM_MODEL_NAME": ("models", "llm", "model_name"),
    "PERSONAL_KB_MODEL_LLM_RUNTIME": ("models", "llm", "runtime"),
    "PERSONAL_KB_MODEL_LLM_QUANTIZATION": ("models", "llm", "quantization"),
    "PERSONAL_KB_MODEL_LLM_ROLE": ("models", "llm", "role"),
    "PERSONAL_KB_MODEL_EMBEDDING_PROVIDER": ("models", "embedding", "provider"),
    "PERSONAL_KB_MODEL_EMBEDDING_MODEL_NAME": ("models", "embedding", "model_name"),
    "PERSONAL_KB_MODEL_EMBEDDING_DIMENSION": ("models", "embedding", "dimension"),
    "PERSONAL_KB_MODEL_RERANKER_PROVIDER": ("models", "reranker", "provider"),
    "PERSONAL_KB_MODEL_RERANKER_MODEL_NAME": ("models", "reranker", "model_name"),
    "PERSONAL_KB_SEARCH_DEFAULT_TOP_K": ("search", "default_top_k"),
    "PERSONAL_KB_SEARCH_INCLUDE_RELATED_DOCUMENTS": (
        "search",
        "include_related_documents",
    ),
    "PERSONAL_KB_SEARCH_INCLUDE_CHUNKS": ("search", "include_chunks"),
    "PERSONAL_KB_SEARCH_SCORE_MODE": ("search", "score_mode"),
    "PERSONAL_KB_SEARCH_GRAPH_SCORE": ("search", "weights", "graph_score"),
    "PERSONAL_KB_SEARCH_VECTOR_SCORE": ("search", "weights", "vector_score"),
    "PERSONAL_KB_SEARCH_ENTITY_SCORE": ("search", "weights", "entity_score"),
    "PERSONAL_KB_SEARCH_TAG_SCORE": ("search", "weights", "tag_score"),
    "PERSONAL_KB_SEARCH_TITLE_KEYWORD_SCORE": (
        "search",
        "weights",
        "title_keyword_score",
    ),
    "PERSONAL_KB_SEARCH_RERANKER_SCORE": ("search", "weights", "reranker_score"),
    "PERSONAL_KB_NORMALIZATION_TAG_ENTITY": (
        "normalization",
        "tag_entity_normalization",
    ),
}


class ConfigLoader:
    """Load YAML configuration into a validated :class:`AppConfig`."""

    def __init__(
        self,
        project_root: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.project_root = (project_root or Path.cwd()).resolve()
        self.env = env if env is not None else os.environ

    def load(self, path: str | Path | None = None) -> AppConfig:
        config_path = self._resolve_config_path(path)
        raw_config = self._read_yaml(config_path)
        normalized = self._normalize_config(raw_config, config_path)
        overrides = self._collect_env_overrides(include_config_path=path is None)
        merged = self._deep_merge(normalized, overrides)
        try:
            return AppConfig.model_validate(merged)
        except ValidationError as exc:
            raise ConfigError(f"invalid configuration in {config_path}: {exc}") from exc

    def _resolve_config_path(self, path: str | Path | None) -> Path:
        candidate = path or self.env.get("PERSONAL_KB_CONFIG") or _DEFAULT_CONFIG_PATH
        config_path = Path(candidate)
        if not config_path.is_absolute():
            config_path = self.project_root / config_path
        return config_path.resolve(strict=False)

    def _read_yaml(self, path: Path) -> dict[str, object]:
        if not path.exists():
            raise ConfigError(f"configuration file not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid YAML in configuration file {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"configuration file must contain a mapping: {path}")
        return data

    def _normalize_config(
        self, raw_config: dict[str, object], config_path: Path
    ) -> dict[str, object]:
        project = self._as_dict(raw_config.get("project"))
        project.setdefault("name", "personal_kb")
        project.setdefault("config_path", self._relativize(config_path))
        project.setdefault("path_mode", "relative")

        storage = self._as_dict(raw_config.get("storage"))
        storage.setdefault("data_dir", "data")
        storage.setdefault("kb_storage_dir", "kb_storage")
        storage.setdefault("benchmark_dir", "benchmark")

        neo4j = self._as_dict(raw_config.get("neo4j"))
        neo4j.setdefault("uri", "bolt://localhost:7687")
        neo4j.setdefault("username", "neo4j")
        neo4j.setdefault("password", "change-me")
        neo4j.setdefault("database", "knowledge_base3")
        neo4j.setdefault("fallback_database", "neo4j")

        llm_source = self._as_dict(raw_config.get("llm"))
        lm_studio = self._as_dict(raw_config.get("lm_studio"))
        llm = {
            "provider": llm_source.get("provider", "lmstudio_openai_compatible"),
            "base_url": llm_source.get(
                "base_url", lm_studio.get("base_url", "http://localhost:1234/v1")
            ),
            "model_name": llm_source.get(
                "model_name",
                lm_studio.get("model", "mlx-community/Qwen3.5-9B-OptiQ-4bit"),
            ),
            "runtime": llm_source.get("runtime", "mlx-lm"),
            "quantization": llm_source.get("quantization", "mixed_precision_4bit"),
            "role": llm_source.get("role", "production_default"),
        }

        embedding_source = self._as_dict(raw_config.get("embedding"))
        embedding = {
            "provider": embedding_source.get("provider", "local"),
            "model_name": embedding_source.get(
                "model_name", "Qwen/Qwen3-Embedding-0.6B"
            ),
            "dimension": embedding_source.get("dimension", 1024),
            "context_length": embedding_source.get("context_length", 32768),
            "normalize_embeddings": embedding_source.get("normalize_embeddings", True),
            "instruction_aware": embedding_source.get("instruction_aware", True),
            "store_full_vectors_in_json": embedding_source.get(
                "store_full_vectors_in_json", True
            ),
        }

        reranker_source = self._as_dict(raw_config.get("reranker"))
        reranker = {
            "provider": reranker_source.get("provider", "local"),
            "model_name": reranker_source.get(
                "model_name", "Qwen/Qwen3-Reranker-0.6B"
            ),
            "context_length": reranker_source.get("context_length", 32768),
            "top_k_before_rerank": reranker_source.get("top_k_before_rerank", 50),
            "top_k_after_rerank": reranker_source.get("top_k_after_rerank", 8),
            "instruction_aware": reranker_source.get("instruction_aware", True),
        }

        search = self._as_dict(raw_config.get("search"))
        search.setdefault("default_top_k", 10)
        search.setdefault("include_related_documents", True)
        search.setdefault("include_chunks", True)
        search.setdefault("score_mode", "hybrid_formula_with_reranker")
        search.setdefault("weights", {})

        normalization = self._as_dict(raw_config.get("normalization"))
        normalization.setdefault(
            "tag_entity_normalization", "lowercase_trim_collapse_spaces"
        )

        return {
            "project": project,
            "storage": storage,
            "neo4j": neo4j,
            "models": {
                "llm": llm,
                "embedding": embedding,
                "reranker": reranker,
            },
            "search": search,
            "normalization": normalization,
        }

    def _collect_env_overrides(self, include_config_path: bool) -> dict[str, object]:
        overrides: dict[str, object] = {}
        for env_name, path in {**_LEGACY_ENV_TO_PATHS, **_PREFERRED_ENV_TO_PATHS}.items():
            if not include_config_path and env_name == "PERSONAL_KB_CONFIG":
                continue
            if env_name not in self.env:
                continue
            value = self._parse_env_value(self.env[env_name])
            self._set_nested(overrides, path, value)
        return overrides

    def _set_nested(
        self, target: dict[str, object], path: tuple[str, ...], value: object
    ) -> None:
        cursor: dict[str, object] = target
        for key in path[:-1]:
            child = cursor.get(key)
            if not isinstance(child, dict):
                child = {}
                cursor[key] = child
            cursor = child
        cursor[path[-1]] = value

    def _deep_merge(
        self, base: dict[str, object], overrides: dict[str, object]
    ) -> dict[str, object]:
        merged = deepcopy(base)
        self._merge_into(merged, overrides)
        return merged

    def _merge_into(
        self, target: dict[str, object], overrides: dict[str, object]
    ) -> None:
        for key, value in overrides.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_into(
                    cast(dict[str, object], target[key]),
                    cast(dict[str, object], value),
                )
            else:
                target[key] = value

    def _parse_env_value(self, raw_value: str) -> object:
        try:
            return yaml.safe_load(raw_value)
        except yaml.YAMLError:
            return raw_value

    def _relativize(self, path: Path) -> str:
        try:
            return path.resolve(strict=False).relative_to(self.project_root).as_posix()
        except ValueError:
            return path.as_posix()

    def _as_dict(self, value: object) -> dict[str, object]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ConfigError("configuration sections must be mappings")
        return dict(value)


def load_config(path: str | Path | None = None) -> AppConfig:
    """Convenience wrapper for loading configuration from the current project."""

    return ConfigLoader().load(path)
